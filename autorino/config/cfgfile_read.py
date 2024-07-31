#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 15:47:05 2022

@author: psakic
"""

import collections.abc
# Create a logger object.
import logging
import os

import yaml

import autorino.common as arocmn
import autorino.convert as arocnv
import autorino.download as arodwl
import autorino.handle as arohdl

# import autorino.session as aroses
# import autorino.epochrange as aroepo
logger = logging.getLogger(__name__)

def run_steps(steps_lis, step_select=[], print_table=True):
    """
    Executes the steps in the provided list.

    This function takes a list of StepGnss objects, an optional list of selected steps,
     and an optional boolean flag for printing tables.
    It iterates over the list of StepGnss objects and executes
    the 'download' or 'convert' method depending on the type of the step.
    If a list of selected steps is provided, only the steps in the list will be executed.
    If the 'print_table' flag is set to True, the tables will be printed during the execution of the steps.

    Parameters
    ----------
    steps_lis : list
        A list of StepGnss objects to be executed.
    step_select : list, optional
        A list of selected steps to be executed. If not provided, all steps in 'steps_lis' will be executed.
        Default is an empty list.
    print_table : bool, optional
        A flag indicating whether to print the tables during the execution of the steps. Default is True.

    Returns
    -------
    None
    """
    wkf_prev = None
    for istp, stp in enumerate(steps_lis):
        if istp > 0:
            wkf_prev = steps_lis[istp - 1]

        if step_select and stp.get_step_type() not in step_select:
            continue

        if stp.get_step_type() == "download":
            stp.download(print_table)
        elif stp.get_step_type() == "convert":
            stp.load_table_from_prev_step_table(wkf_prev.table)
            stp.convert(print_table)


def read_cfg(configfile_path, epoch_range=None, main_cfg_path=None):
    """
    Load a configuration file (YAML format) and return a list of StepGnss objects to be launched sequentially.

    This function takes in a path to a configuration file, an optional EpochRange object, and an optional path
    to a main configuration file.
    It reads the configuration file, updates it with the main configuration file if provided,
    and creates a list of StepGnss objects based on the configuration.
    The EpochRange object, if provided, will override the epoch ranges given in the configuration file.

    Parameters
    ----------
    configfile_path : str
        The path to the configuration file.
    epoch_range : EpochRange, optional
        An EpochRange object which will override the epoch ranges given in the configuration file. Default is None.
    main_cfg_path : str, optional
        The path to the main configuration file. Default is None.

    Returns
    -------
    steps_lis_lis : list
        A list of lists of StepGnss objects to be launched sequentially.
    steps_dic_dic : dict
        A dictionary of dictionaries of StepGnss.
    y_station : dict
        A dictionary of station information.
    """
    global y_main
    logger.info("start to read configfile: %s", configfile_path)

    y = yaml.safe_load(open(configfile_path))

    if main_cfg_path:
        y_main = yaml.safe_load(open(main_cfg_path))
        y_main_sessions = y_main["station"]["sessions"]
    else:
        y_main_sessions = None

    y = update_w_main_dic(y, y_main)
    print(y)
    y_station = y["station"]

    steps_lis_lis, steps_dic_dic = read_cfg_sessions(
        y_station["sessions"], y_station=y_station, epoch_range=epoch_range
    )

    return steps_lis_lis, steps_dic_dic, y_station


def read_cfg_sessions(y_sessions_dict, epoch_range=None, y_station=None):
    steps_lis_lis = []
    steps_dic_dic = {}

    for k_ses, y_ses in y_sessions_dict.items():

        y_gen = y_ses["general"]
        # y_gen_main = y_ses_main['general']
        # y_gen = update_w_main_dic(y_gen, y_gen_main)

        ##### TMP DIRECTORY
        tmp_dir, _, _ = _get_dir_path(y_gen, "tmp")

        ##### LOG DIRECTORY
        log_dir, _, _ = _get_dir_path(y_gen, "log")

        ##### EPOCH RANGE AT THE SESSION LEVEL
        if not epoch_range:
            epo_obj_ses = _epoch_range_from_cfg_bloc(y_ses["epoch_range"])
        else:
            epo_obj_ses = epoch_range

        steps_lis = []
        steps_dic = {}

        #### manage steps
        y_steps = y_ses["steps"]
        # y_workflow_main = y_ses_main['workflow']

        for k_stp, y_stp in y_steps.items():
            logger.debug("k_stp, y_stp AAA %s %s ", k_stp, y_stp)

            # y_step_main = y_workflow_main[k_stp]
            # y_step = update_w_main_dic(y_step, y_step_main)

            ##### EPOCH RANGE AT THE STEP LEVEL

            if y_stp["epoch_range"] == "FROM_SESSION":
                epo_obj_stp = epo_obj_ses
                y_stp["epoch_range"] = y_ses["epoch_range"]
            else:
                epo_obj_stp = _epoch_range_from_cfg_bloc(y_stp["epoch_range"])

            out_dir, _, _ = _get_dir_path(y_stp, "out")
            inp_dir, inp_dir_parent, inp_structure = _get_dir_path(
                y_stp, "inp", check_parent_dir_existence=False
            )

            if k_stp == "download":
                if not _is_cfg_bloc_active(y_stp):
                    continue

                dwl = arodwl.DownloadGnss
                step_obj = dwl(
                    out_dir=out_dir,
                    tmp_dir=tmp_dir,
                    log_dir=log_dir,
                    epoch_range=epo_obj_stp,
                    access=y_station["access"],
                    inp_dir_parent=inp_dir_parent,
                    inp_structure=inp_structure,
                    site=y_station["site"],
                    session=y_ses["general"],
                    options=y_stp["options"],
                )

            # appended in lis and dic at the end of the tests

            elif k_stp == "convert":
                if not _is_cfg_bloc_active(y_stp):
                    continue

                if y_station["site"]["sitelog_path"]:
                    sitelogs = y_station["site"]["sitelog_path"]
                else:
                    sitelogs = None

                cnv = arocnv.ConvertGnss
                step_obj = cnv(
                    out_dir=out_dir,
                    tmp_dir=tmp_dir,
                    log_dir=log_dir,
                    epoch_range=epo_obj_stp,
                    site=y_station["site"],
                    session=y_ses["general"],
                    metadata=sitelogs,
                    options=y_stp["options"],
                )

            elif k_stp == "split":
                if not _is_cfg_bloc_active(y_stp):
                    continue

                if y_station["site"]["sitelog_path"]:
                    sitelogs = y_station["site"]["sitelog_path"]
                else:
                    sitelogs = None

                spl = arohdl.HandleGnss
                step_obj = spl(
                    out_dir=out_dir,
                    tmp_dir=tmp_dir,
                    log_dir=log_dir,
                    epoch_range=epo_obj_stp,
                    site=y_station["site"],
                    session=y_ses["general"],
                    metadata=sitelogs,
                    options=y_stp["options"],
                )

                # appended in lis and dic at the end of the k_stp tests

            else:
                logger.warning("unknown step %s in config file, skipped...", k_stp)
                continue

            steps_lis.append(step_obj)
            steps_dic[k_stp] = step_obj

        steps_lis_lis.append(steps_lis)
        steps_dic_dic[k_ses] = steps_dic

    return steps_lis_lis, steps_dic_dic


def _check_parent_dir_existence(parent_dir):
    """
    Checks if a parent directory exists and translates it with the environment variable first.

    This function takes a string representing a directory path.
    It first translates the directory path with the environment variable.
    Then, it checks if the translated directory exists.
    If it does not exist, it raises a FileNotFoundError with a custom error message.
    If it does exist, it returns None.

    This function is an internal function for the read_cfg function.

    Will translate it with the environment variable first.

    Parameters
    ----------
    parent_dir : str
        A string representing a directory path.

    Raises
    ------
    FileNotFoundError
        If the translated directory does not exist.

    Returns
    -------
    None
        If the translated directory exists.
    """
    parent_dir_out = arocmn.translator(parent_dir)

    if not os.path.isdir(parent_dir_out):
        logger.error("%s do not exists, create it first", parent_dir_out)
        raise FileNotFoundError(
            None, parent_dir_out + " do not exists, create it first"
        )
    else:
        return None


def _is_cfg_bloc_active(ywkf):
    """
    Checks if a configuration block is active.

    This function takes a dictionary representing a configuration block.
    It checks if the 'active' key is present in the dictionary.
    If it is, it returns the value of the 'active' key.
    If the 'active' key is not present,
    it assumes the block is active and returns True.

    Internal function for read_cfg

    Parameters
    ----------
    ywkf : dict
        A dictionary representing a configuration block.

    Returns
    -------
    bool
        True if the 'active' key is present and its value is True,
        or if the 'active' key is not present.
        False if the 'active' key is present and its value is False.
    """
    if "active" in ywkf.keys():
        if ywkf["active"]:
            return True
        else:
            return False
    else:  ### if no 'active' key, we assume the bloc active
        return True


def _epoch_range_from_cfg_bloc(epoch_range_dic):
    """
    get an EpochRange object from epoch_range dictionary bloc
    internal function for read_cfg

    """
    return arocmn.EpochRange(
        epoch_range_dic["epoch1"],
        epoch_range_dic["epoch2"],
        epoch_range_dic["period"],
        epoch_range_dic["round_method"],
        epoch_range_dic["tz"],
    )


def _get_dir_path(y_step, dir_type="out", check_parent_dir_existence=True):
    """
    Constructs a directory path based on the provided parameters.

    This function takes a dictionary containing step information,
     a directory type, and a flag indicating whether to check if
     the parent directory exists. It constructs a directory
     path by joining the parent directory and the structure.
     If the flag to check the existence of the parent directory
     is set to True, it checks if the parent directory exists.

    Parameters
    ----------
    y_step : dict
        A dictionary containing step information.
    dir_type : str, optional
        The type of directory to be constructed. Default is 'out'.
    check_parent_dir_existence : bool, optional
        A flag indicating whether to check if the parent directory exists.
        Default is True.

    Returns
    -------
    tuple
        A tuple containing the constructed directory path,
        the parent directory, and the structure.
    """
    dir_parent = y_step[dir_type + "_dir_parent"]
    structure = y_step[dir_type + "_structure"]
    if check_parent_dir_existence:
        _check_parent_dir_existence(dir_parent)
    dir_path = os.path.join(dir_parent, structure)

    return dir_path, dir_parent, structure


def update_w_main_dic(d, u=None, specific_value="FROM_MAIN"):
    if u is None:
        return d
    for k, v in u.items():
        if not k in d.keys():
            continue
        if d[k] == specific_value:
            print("AAAAAAAAAAAAAA", specific_value)
            d[k] = v
        elif isinstance(v, collections.abc.Mapping):
            d[k] = update_w_main_dic(d.get(k, {}), v)
        else:
            if d[k] == specific_value:
                print("AAAAAAAAAAAAAA", specific_value)
                d[k] = v
    return d
