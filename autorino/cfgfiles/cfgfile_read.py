#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 15:47:05 2022

@author: psakic
"""

import collections.abc

# Create a logger object.
import os
import yaml
import mergedeep
from pprint import pprint

import autorino.common as arocmn
import autorino.convert as arocnv
import autorino.download as arodwl
import autorino.handle as arohdl

#### new rinexmod v4 import
import rinexmod.api as rimo_api
import rinexmod.classes as rimo_cls
#### old rinexmod import (for compatibility with older versions)
#from rinexmod import rinexmod_api as rimo_api
#from rinexmod import metadata as rimo_mda

import datetime as dt

#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger("autorino")
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])

BOLD_SRT = "\033[1m"
BOLD_END = "\033[0m"


def load_cfg(cfg_path, verbose=True):
    """
    Loads quickly one or several configuration files (YAML format) **without interpretation**.

    This function reads a YAML configuration file from the specified path and returns the parsed content.

    Parameters
    ----------
    cfg_path : str or list of str
        The path(s) to the configuration file.
        If a list is provided, the config files are merged
    verbose : bool

    Returns
    -------
    dict
        The parsed/merged content of the configuration files.
    """

    recursive = True if isinstance(cfg_path, list) else False

    if verbose and not recursive:
        logger.info(BOLD_SRT + ">>>>>>>> Read configfile: " + BOLD_END + "%s", cfg_path)
    if recursive:
        ys_raw = [y for y in [load_cfg(c, verbose=verbose) for c in cfg_path] if y]
        return mergedeep.merge({}, *ys_raw)
    elif not cfg_path or not os.path.isfile(cfg_path):
        msg = f"config file doesn't exists!: {cfg_path}"
        logger.error(msg)
        raise FileNotFoundError(None, msg)
    else:
        y_out = yaml.safe_load(open(cfg_path))
        return y_out


def read_cfg(
    site_cfg_path, epoch_range=None, include_cfg_paths_xtra=None, verbose=False
):
    """
    Read and interpret a configuration file (YAML format) and
    return a list of StepGnss objects to be launched sequentially.

    This function takes in a path to a configuration file,
    an optional EpochRange object, and an optional path
    to a main configuration file.
    It reads the configuration file, updates it with the main configuration file if provided,
    and creates a list of StepGnss objects based on the configuration.
    The EpochRange object, if provided, will override the epoch ranges given in the configuration file.

    Parameters
    ----------
    site_cfg_path : str
        The path to the configuration file.
        Should be a single file here (no list).
    epoch_range : EpochRange, optional
        An EpochRange object which will override the epoch ranges
        given in the configuration file. Default is None.
    include_cfg_paths_xtra : str or list of str, optional
        The path to the include configuration file.
        If a list is provided, the include config files are merged.
        It overrides the files given with the 'include' keyword
        in the site configuration file.
        Default is None.
    verbose : bool, optional
        A flag indicating whether to print the configuration

    Returns
    -------
    steps_lis_lis : list
        A list of lists of StepGnss objects to be launched sequentially.
    steps_dic_dic : dict
        A dictionary of dictionaries of StepGnss.
    y_use : dict
        The parsed/merged content of the configuration file as dictionary.
    """

    y_site = load_cfg(site_cfg_path)

    if "include" in y_site.keys():
        include_cfg_paths = get_incl_cfg_paths(y_site, site_cfg_path)
        y_incl = load_cfg(include_cfg_paths, verbose=False)
    else:
        y_incl = load_cfg(include_cfg_paths_xtra, verbose=False)

    # before config files v20 (2025-04-10), the keyword FROM_MAIN was used in the sites cfgfiles
    # after v20, the main cfgfile is the basis, and is automatically overloaded with site cfgfile values
    legacy_main_updt = True if float(y_site["cfgfile_version"]) < 20.0 else False
    if legacy_main_updt:  # cfgfile_version < 20.
        y_use = read_cfg_legacy(y_site, y_incl)
    else:  # cfgfile_version >= 20.
        y_use = mergedeep.merge({}, y_incl, y_site) if y_incl else y_site.copy()

    if verbose:
        logger.debug(f"Used configuration (updated with include):\n{yaml.dump(y_use)}")

    steps_lis_lis, steps_dic_dic = read_cfg_core(y_use, epoch_range_inp=epoch_range)

    return steps_lis_lis, steps_dic_dic, y_use


def read_cfg_core(y_inp, epoch_range_inp=None):
    """
    Reads and interprets session configurations from a dictionary
    and returns lists and dictionaries of StepGnss objects.

    This function processes session configurations,
    loads metadata if available, and constructs lists and dictionaries
    of StepGnss objects based on the provided session configurations.

    Parameters
    ----------
    y_inp : dict
        A dictionary a site configuration.
    epoch_range_inp : EpochRange, optional
        An EpochRange object which will override the epoch ranges given
        in the session configurations. Default is None.

    Returns
    -------
    steps_lis_lis : list
        A list of lists of StepGnss objects to be launched sequentially.
    steps_dic_dic : dict
        A dictionary of dictionaries of StepGnss objects.
    """

    # ++++ METADATA
    y_station = y_inp["station"]
    y_sessions = y_station["sessions"]
    # Load metadata as external sitelog(s)
    if y_station["device"]["attributes_from_sitelog"]:
        slpath = y_station["site"]["sitelog_path"]
        if os.path.isdir(slpath) or os.path.isfile(slpath):
            # Load the metadata if the path is a directory or a file
            metadata = rimo_api.metadata_input_manage(slpath, force=False)
        else:
            # If not, keep the path it as a string
            # (because it might contain aliases and be translated later in the object)
            metadata = slpath
    # Load metadata as device block
    else:
        metadata = _device2mda(y_station)

    steps_lis_lis = []
    steps_dic_dic = {}
    for k_ses, y_ses in y_sessions.items():

        steps_lis = []
        steps_dic = {}

        y_gen = y_ses["general"]

        if not _is_cfg_bloc_active(y_gen):
            continue

        # y_gen_main = y_ses_main['general']
        # y_gen = update_w_main_dic(y_gen, y_gen_main)

        # ++++ TMP DIRECTORY
        tmp_dir, _, _ = _get_dir_path(y_gen, "tmp")

        # ++++ LOG DIRECTORY
        log_dir, _, _ = _get_dir_path(y_gen, "log")

        # ++++ EPOCH RANGE AT THE SESSION LEVEL
        if epoch_range_inp:
            epo_obj_ses = epoch_range_inp
        else:
            epo_obj_ses = _epoch_range_from_cfg_bloc(y_ses["epoch_range"])

        # ++++ manage steps
        y_steps = y_ses["steps"]
        # y_workflow_main = y_ses_main['workflow']

        for k_stp, y_stp in y_steps.items():
            # y_step_main = y_workflow_main[k_stp]
            # y_step = update_w_main_dic(y_step, y_step_main)

            if not _is_cfg_bloc_active(y_stp):
                continue

            # ++++ EPOCH RANGE AT THE STEP LEVEL
            step_cls = step_cls_select(k_stp)
            if not step_cls:
                logger.warning("unknown step %s, skip", k_stp)
                continue

            if (
                y_stp["epoch_range"] == "FROM_SESSION"
                or not "epoch_range" in y_stp.keys()
            ):
                epo_obj_stp = epo_obj_ses
                y_stp["epoch_range"] = y_ses["epoch_range"]
            else:
                epo_obj_stp = _epoch_range_from_cfg_bloc(y_stp["epoch_range"])

            ## concatenate the dir_parent and the structure
            # (but not the file_regex, it is just about the directory)
            out_dir, _, _ = _get_dir_path(y_stp, "out")
            inp_dir, _, _ = _get_dir_path(y_stp, "inp", check_parent_dir_exist=False)

            if "inp_file_regex" in y_stp.keys():
                inp_file_regex = y_stp["inp_file_regex"]
            else:
                logger.warning("Compatibility! inp_file_regex not defined in cfg files")
                logger.warning("upgrade your config file to >v15, set to .* for now")
                inp_file_regex = ".*"

            kwargs_for_step = {
                "out_dir": out_dir,
                "tmp_dir": tmp_dir,
                "log_dir": log_dir,
                "inp_dir": inp_dir,
                "inp_file_regex": inp_file_regex,
                "epoch_range": epo_obj_stp,
                "site": y_station["site"],
                "session": y_ses["general"],
                "options": y_stp["options"],
                "metadata": metadata,
            }

            if k_stp == "download":
                kwargs_for_step["access"] = y_station["access"]

            ### +++ CREATION OF THE OBJECT ###########
            step_obj = step_cls(**kwargs_for_step)
            ##########################################
            # appended in lis and dic at the end of the k_stp tests
            steps_lis.append(step_obj)
            steps_dic[k_stp] = step_obj

        steps_lis_lis.append(steps_lis)
        steps_dic_dic[k_ses] = steps_dic

    return steps_lis_lis, steps_dic_dic


def step_cls_select(step_name):
    """
    Selects the appropriate class for a given step name.

    This function maps a step name to its corresponding class, which is used
    to handle specific GNSS processing steps such as 'download', 'convert',
    'split', or 'splice'. If the step name is unknown, a warning is logged,
    and None is returned.

    Parameters
    ----------
    step_name : str
        The name of the step for which the corresponding class is to be selected.

    Returns
    -------
    class or None
        The class corresponding to the given step name, or None if the step name is unknown.

    Notes
    -----
    - Supported step names and their corresponding classes:
        - 'download': arodwl.DownloadGnss
        - 'convert': arocnv.ConvertGnss
        - 'split': arohdl.SplitGnss
        - 'splice': arohdl.SpliceGnss
    - Logs a warning if the step name is not recognized.
    """
    if step_name == "download":
        return arodwl.DownloadGnss
    elif step_name == "convert":
        return arocnv.ConvertGnss
    elif step_name == "split":
        return arohdl.SplitGnss
    elif step_name == "splice":
        return arohdl.SpliceGnss
    elif step_name in ("modify", "rinexmod"):
        if step_name == "rinexmod":
            warnmsg = "step 'rinexmod' is deprecated, use 'modify' instead"
            logger.warning(warnmsg)
            DeprecationWarning(warnmsg)
        return arohdl.ModifyGnss
    else:
        logger.warning("unknown step %s in cfgfiles file, skip", step_name)
        return None


def run_steps(
    steps_lis,
    steps_select_list=None,
    exclude_steps_select=False,
    verbose=True,
    force=False,
):
    """
    Executes the steps in the provided list.

    This function takes a list of StepGnss objects,
    an optional list of selected steps,
    and an optional boolean flag for printing tables.
    It iterates over the list of StepGnss objects and executes
    the 'download' or 'convert' method depending on the type of the step.
    If a list of selected steps is provided,
    only the steps in the list will be executed.
    If the 'verbose' flag is set to True,
    the tables will be printed during the execution of the steps.

    Parameters
    ----------
    steps_lis : Iterable
        A list of StepGnss objects to be executed.
    steps_select_list : list, optional
        A list of selected steps to be executed.
        If not provided, all steps in 'steps_lis' will be executed.
        Default is None.
    exclude_steps_select : bool, optional
        If True the selected steps indicated in step_select_list are excluded.
        It is the opposite behavior of the regular one using steps_list
        Default is False.
    verbose : bool, optional
        A flag indicating whether to print the tables during the execution of the steps.
         Default is True.
    force : bool, optional
        A flag indicating whether to force the execution of the steps.
        overrides the 'force' parameters in the configuration file.
        Default is False.

    Returns
    -------
    None
    """

    # If no steps are selected, initialize an empty list
    if not steps_select_list:
        steps_select_list = []

    wkf_prev = None

    # Log the number of steps to be run
    logger.info("%i steps will be run %s", len(steps_lis), steps_lis)

    # Iterate over the list of steps
    for istp, stp in enumerate(steps_lis):
        if istp > 0:
            wkf_prev = steps_lis[istp - 1]

        # Check if there are selected steps to be run
        if len(steps_select_list) > 0:
            # Forced case: steps_list contains the steps to be run only
            if (
                not exclude_steps_select
                and stp.get_step_type() not in steps_select_list
            ):
                logger.warning(
                    "step %s skipped, not selected in %s",
                    stp.get_step_type(),
                    steps_select_list,
                )
                continue
            # Exclusion case: steps_list contains steps to be excluded
            elif exclude_steps_select and stp.get_step_type() in steps_select_list:
                logger.warning(
                    "step %s skipped, selected in %s",
                    stp.get_step_type(),
                    steps_select_list,
                )
                continue
            else:
                pass

        # Set the verbose option if verbose is True
        if verbose:
            stp.options["verbose"] = True

        if force:
            stp.options["force"] = True

        load_table_msg_str = BOLD_SRT + ">>>>>>>> Load table for step %s" + BOLD_END
        # Execute the step based on its type
        if stp.get_step_type() == "download":
            stp.download(**stp.options)
        elif stp.get_step_type() == "convert":
            logger.info(load_table_msg_str, stp.get_step_type())
            stp.load_tab_inpdir()
            stp.convert(**stp.options)
        elif stp.get_step_type() == "splice":
            stp_rnx_inp = stp.copy()
            logger.info(load_table_msg_str, stp.get_step_type())
            stp_rnx_inp.load_tab_inpdir(update_epochs=True)
            stp.splice(input_mode="given", input_rinexs=stp_rnx_inp, **stp.options)
        elif stp.get_step_type() == "split":
            stp_rnx_inp = stp.copy()
            logger.info(load_table_msg_str, stp.get_step_type())
            stp_rnx_inp.load_tab_inpdir(update_epochs=True)
            stp.split(input_mode="given", input_rinexs=stp_rnx_inp, **stp.options)
        elif stp.get_step_type() in ("modify", "rinexmod"):
            if stp.get_step_type()  == "rinexmod":
                warnmsg = "step 'rinexmod' is deprecated, use 'modify' instead"
                logger.warning(warnmsg)
                DeprecationWarning(warnmsg)
            stp.load_tab_inpdir(update_epochs=True)
            stp.modify(**stp.options)

        ##### close the step

    return None


def _chk_parent_dir(parent_dir, parent_dir_key=None):
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
    parent_dir_key : str, optional
        The dictionnary key representing the parent directory.
        Default is None.

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

    mkdir_err_msg = " does not exists, create it manually first (mkdir -p ...)"

    ### FROM_MAIN is obsolete, this if test too
    # if parent_dir_out == "FROM_MAIN":
    #     # case when the parent directory is not defined in the main cfgfiles file
    #
    #     if not parent_dir_key:
    #         parent_dir_key = "a directory"
    #
    #     logger.error(
    #         "%s is not correctly defined in the main cfgfiles file "
    #         "(FROM_MAIN can not be replaced)",
    #         parent_dir_key,
    #     )
    #     raise FileNotFoundError(None, parent_dir_key + mkdir_err_msg)

    if not os.path.isdir(parent_dir_out):
        logger.error(parent_dir_out + mkdir_err_msg)
        raise FileNotFoundError(None, parent_dir_out + mkdir_err_msg)
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
    else:  # ++++ if no 'active' key, we assume the bloc active
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


def _get_dir_path(y_step, dir_type="out", check_parent_dir_exist=True):
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
    check_parent_dir_exist : bool, optional
        A flag indicating whether to check if the parent directory exists.
        Default is True.

    Returns
    -------
    tuple
        A tuple containing the constructed directory path,
        the parent directory, and the structure.
    """

    def _key_check(key_inp, y_step_inp):
        if not key_inp in y_step_inp.keys():
            logger.error(f"no {key_parent} in {y_step}")
        return None

    key_parent = dir_type + "_dir_parent"
    key_structure = dir_type + "_dir_structure"

    _key_check(key_parent, y_step)
    dir_parent = y_step[key_parent]

    _key_check(key_structure, y_step)
    structure = y_step[key_structure]

    if check_parent_dir_exist:
        _chk_parent_dir(dir_parent, parent_dir_key=dir_type + "_dir_parent")

    dir_parent, structure = format_dir_path(dir_parent, structure)

    dir_path = os.path.join(dir_parent, structure)

    return dir_path, dir_parent, structure


def _device2mda(y_station):
    """
    Convert a device block from a configuration file to a MetaData object.
    """
    y_dev = y_station["device"]
    y_sit = y_station["site"]

    for attkw in ["rec_type", "rec_sn", "rec_fw", "ant_type", "ant_sn"]:
        if not attkw in y_dev.keys():
            logger.warning(
                "device attribute %s not found in cfg file, set to 'unknown'", attkw
            )
            y_dev[attkw] = "unknown"

    metadata = rimo_cls.MetaData()
    rec_dic = dict()
    rec_dic["Receiver Type"] = y_dev["rec_type"]
    rec_dic["Serial Number"] = str(y_dev["rec_sn"])
    rec_dic["Firmware Version"] = str(y_dev["rec_fw"])

    if not "rec_sat_sys" in y_dev.keys():
        rec_dic["Satellite System"] = "GPS+GLO+GAL+BDS+QZSS+SBAS"
    else:
        rec_dic["Satellite System"] = y_dev["rec_sat_sys"]

    ant_dic = dict()
    ant_dic["Antenna Type"] = y_dev["ant_type"]
    ant_dic["Antenna Radome Type"] = y_dev["ant_type"][-4:]

    ant_dic["Serial Number"] = y_dev["ant_sn"]

    ant_dic["Marker->ARP Up Ecc. (m)"] = y_dev["ecc_une"][0]
    ant_dic["Marker->ARP North Ecc(m)"] = y_dev["ecc_une"][1]
    ant_dic["Marker->ARP East Ecc(m)"] = y_dev["ecc_une"][2]

    metadata.add_instru(rec_dic, ant_dic)

    metadata.set_meta(
        site_id=y_sit["site_id"],
        domes=y_sit["domes"],
        operator=y_sit["operator"],
        x=y_sit["position_xyz"][0],
        y=y_sit["position_xyz"][1],
        z=y_sit["position_xyz"][2],
        country=y_sit["country"],
        date_prepared=dt.datetime.now(),
        agency=y_sit["agency"],
    )

    return metadata


def format_dir_path(dir_parent, structure):
    """
    Formats a directory path by adding or removing a leading slash.
    """

    if dir_parent[0] != "/":
        logger.warning(
            "dir_parent %s should start with slash (/), we add it automatically",
            dir_parent,
        )
        dir_parent = "/" + dir_parent

    if structure and structure[0] == "/":
        logger.warning(
            "structure %s should not start with slash (/), we remove it automatically",
            structure,
        )
        structure = structure[1:]

    return dir_parent, structure


def get_incl_cfg_paths(y_inp, site_cfg_path):
    """
    Generates a list of absolute paths for included configuration files.

    This function processes the 'include' section of a configuration dictionary,
    translates the paths using a translator function, and converts them to
    absolute paths relative to the provided site configuration file path.

    Parameters
    ----------
    y_inp : dict
        A dictionary containing the configuration data, including an 'include' key
        with paths to additional configuration files.
    site_cfg_path : str
        The absolute path to the site configuration file.

    Returns
    -------
    list
        A list of absolute paths for the included configuration files.
    """
    incl_cfg_paths_out = []
    for p in y_inp["include"]:
        # Translate the path using a custom translator function
        pmod = arocmn.translator(p)
        # Convert the path to be relative to the site configuration file's directory
        pmod = os.path.join(os.path.dirname(site_cfg_path), pmod)
        # Ensure the path is absolute with respect to the site configuration file
        pmod = arocmn.abs_path_wrt(pmod, site_cfg_path)
        incl_cfg_paths_out.append(pmod)
    return incl_cfg_paths_out


def get_incl_strategy(strat_str):
    """
    Retrieves the merging strategy for configuration files.

    This function maps a string representing a merging strategy to the corresponding
    `mergedeep.Strategy` enum value. Supported strategies are 'append' and 'replace'.

    Parameters
    ----------
    strat_str : str
        The merging strategy as a string. Valid values are 'append' or 'replace'.

    Returns
    -------
    mergedeep.Strategy
        The corresponding merging strategy.

    Raises
    ------
    ValueError
        If the provided strategy string is invalid.
    """
    if strat_str == "append":
        return mergedeep.Strategy.APPEND
    elif strat_str == "replace":
        return mergedeep.Strategy.REPLACE
    else:
        raise ValueError(
            f"Invalid strategy '{strat_str}'. "
            "Valid strategies are 'append' or 'replace'."
        )


#  _                                    __                  _   _
# | |                                  / _|                | | (_)
# | |     ___  __ _  __ _  ___ _   _  | |_ _   _ _ __   ___| |_ _  ___  _ __  ___
# | |    / _ \/ _` |/ _` |/ __| | | | |  _| | | | '_ \ / __| __| |/ _ \| '_ \/ __|
# | |___|  __/ (_| | (_| | (__| |_| | | | | |_| | | | | (__| |_| | (_) | | | \__ \
# |______\___|\__, |\__,_|\___|\__, | |_|  \__,_|_| |_|\___|\__|_|\___/|_| |_|___/
#              __/ |            __/ |
#             |___/            |___/


def check_from_main(y):
    """
    Check if the FROM_MAIN keyword is used in the configuration file.

    This function takes a dictionary representing the configuration file.
    It checks if the 'FROM_MAIN' keyword is used in the configuration file.
    If it is, it returns True. Otherwise, it returns False.

    Parameters
    ----------
    y : dict
        A dictionary representing the configuration file.

    Returns
    -------
    bool
        True if the 'FROM_MAIN' keyword is used in the configuration file.
        False otherwise.

    Warning
    -------
    Obsolete since 2025-04 and cfgfile v >= 20.0
    """
    if "FROM_MAIN" in str(y):
        return True
    else:
        return False


def update_w_main_dic(d, u=None, specific_value="FROM_MAIN"):
    """
    Updates a dictionary with another dictionary.

    Warning
    -------
    Obsolete since 2025-04 and cfgfile v >= 20.0
    """
    if u is None:
        return d
    for k, v in u.items():
        if k not in d.keys():
            continue
        if d[k] == specific_value:
            d[k] = v
        elif isinstance(v, collections.abc.Mapping):
            d[k] = update_w_main_dic(d.get(k, {}), v)
        else:
            if d[k] == specific_value:
                d[k] = v
    return d


def read_cfg_legacy(y_inp, y_main):
    """
    Handles legacy configuration files with the 'FROM_MAIN' keyword.

    This function processes configuration files with a version less than 20.0,
    where the 'FROM_MAIN' keyword is used to indicate that values should be
    inherited from a main configuration file. If the main configuration file
    is not provided or cannot be found, an error is raised.

    Parameters
    ----------
    y_inp : dict
        The input configuration dictionary (site-specific configuration).
    y_main : dict or None
        The main configuration dictionary. If None, the function will check
        for the presence of the 'FROM_MAIN' keyword in the input configuration.

    Returns
    -------
    dict
        The updated configuration dictionary, where values from the main
        configuration file have been merged into the input configuration.

    Raises
    ------
    FileNotFoundError
        If the 'FROM_MAIN' keyword is used in the input configuration but
        no main configuration file is provided.

    Warning
    -------
    Obsolete since 2025-04 and cfgfile v >= 20.0
    """
    # Log a warning indicating that a legacy configuration file is being used
    logger.warning("Use legacy cfgfile w/ FROM_MAIN keyword (cfgfile_version < 20.)")

    # Check if the main configuration file is missing and the 'FROM_MAIN' keyword is used
    if not y_main and check_from_main(y_inp):
        errmsg = "FROM_MAIN keyword used in cfg file, but no main cfg file provided (-m option)"
        logger.error(errmsg)  # Log an error message
        raise FileNotFoundError(
            None, errmsg
        )  # Raise an exception with the error message

    # Merge the input configuration with the main configuration
    y = update_w_main_dic(y_inp, y_main)

    # Return the updated configuration dictionary
    return y
