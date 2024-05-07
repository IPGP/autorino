#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 15:47:05 2022

@author: psakic
"""

import os
import autorino.common as arocmn
import autorino.download as arodwl
import autorino.convert as arocnv
import autorino.handle as arohdl

#import autorino.session as aroses
#import autorino.epochrange as aroepo

import yaml
import glob
import collections.abc

# Create a logger object.
import logging
logger = logging.getLogger(__name__)

def autorino_run(cfg_in,main_cfg_in):
    if os.path.isdir(cfg_in):
        cfg_use_lis = glob.glob(cfg_in + '/*yml')
    elif os.path.isfile(cfg_in):
        cfg_use_lis = [cfg_in]
    else:
        logger.error("%s does not exist, check input config file/dir", cfg_in)
        raise Exception

    for cfg_use in cfg_use_lis:
        steps_lis_lis, steps_dic_dic, y_station = read_cfg(configfile_path=cfg_use, main_cfg_path=main_cfg_in)
        for steps_lis in steps_lis_lis:
            run_steps(steps_lis)

    return None


def run_steps(steps_lis, print_table=True):
    wkf_prev = None
    for istp, stp in enumerate(steps_lis):
        if istp > 0:
            wkf_prev = steps_lis[istp - 1]

        if stp.get_step_type() == "DownloadGnss":
            stp.download(print_table)
        elif stp.get_step_type() == "ConvertGnss":
            stp.load_table_from_prev_step_table(wkf_prev.table)
            stp.convert(print_table)


def read_cfg(configfile_path,
             epoch_range=None,
             main_cfg_path=None):
    """
    Load a config file (YAML format) and 
    return a "Steps list" i.e. a list of StepGnss object 
    to be launched sequentially
    
    epoch_range_inp is a EpochRange object which will override the epoch ranges
    given in the config file

    Parameters
    ----------
    configfile_path : TYPE
        DESCRIPTION.
    epoch_range_inp : TYPE, optional
        DESCRIPTION. The default is None.

    Returns
    -------
    steps_lis : list
        "Steps list" i.e. a list of StepGnss object 
        to be launched sequentially.
    y_site : dict
        site dictionary.
    y_device : dict
        device dictionary.
    y_access : dict
        station access dictionary.
    """
    global y_main
    logger.info('start to read configfile: %s',
                configfile_path)

    y = yaml.safe_load(open(configfile_path))

    if main_cfg_path:
        y_main = yaml.safe_load(open(main_cfg_path))
        y_main_sessions = y_main['station']['sessions']
    else:
        y_main_sessions = None

    y_station = y["station"]

    y = update_w_main_dic(y, y_main)
    steps_lis_lis, steps_dic_dic = read_cfg_sessions(y_station["sessions"],
                                                     y_station=y_station,
                                                     epoch_range=epoch_range)

    return steps_lis_lis, steps_dic_dic, y_station


def read_cfg_sessions(y_sessions_dict,
                      epoch_range=None,
                      y_station=None):
    steps_lis_lis = []
    steps_dic_dic = {}

    for k_ses, y_ses in y_sessions_dict.items():

        y_gen = y_ses['general']
        #y_gen_main = y_ses_main['general']
        #y_gen = update_w_main_dic(y_gen, y_gen_main)

        ##### TMP DIRECTORY
        tmp_dir, _, _ = _get_dir_path(y_gen, 'tmp')

        ##### LOG DIRECTORY
        log_dir, _, _ = _get_dir_path(y_gen, 'log')

        ##### EPOCH RANGE AT THE SESSION LEVEL
        if not epoch_range:
            epo_obj_ses = _epoch_range_from_cfg_bloc(y_ses['epoch_range'])
        else:
            epo_obj_ses = epoch_range

        steps_lis = []
        steps_dic = {}

        #### manage steps
        y_steps = y_ses['steps']
        #y_workflow_main = y_ses_main['workflow']

        for k_stp, y_stp in y_steps.items():

            #y_step_main = y_workflow_main[k_stp]
            #y_step = update_w_main_dic(y_step, y_step_main)

            ##### EPOCH RANGE AT THE STEP LEVEL
            if y_stp['epoch_range'] == 'FROM_SESSION':
                epo_obj_stp = epo_obj_ses
                y_stp['epoch_range'] = y_ses['epoch_range']
            else:
                epo_obj_stp = _epoch_range_from_cfg_bloc(y_stp['epoch_range'])

            out_dir, _, _ = _get_dir_path(y_stp, 'out')
            inp_dir, inp_dir_parent, inp_structure = _get_dir_path(y_stp,
                                                                   'inp',
                                                                   check_parent_dir_existence=False)

            if k_stp == 'download':
                if not _is_cfg_bloc_active(y_stp):
                    continue

                dwl = arodwl.DownloadGnss
                step_obj = dwl(out_dir=out_dir,
                               tmp_dir=tmp_dir,
                               log_dir=log_dir,
                               epoch_range=epo_obj_stp,
                               access=y_station['access'],
                               remote_dir=inp_dir_parent,
                               remote_fname=inp_structure,
                               site=y_station['site'],
                               session=y_ses['general'],
                               options=y_stp['options'])

            # appended in lis and dic at the end of the tests

            elif k_stp == 'convert':
                if not _is_cfg_bloc_active(y_stp):
                    continue

                if y_station['site']['sitelog_path']:
                    sitelogs = y_station['site']['sitelog_path']
                else:
                    sitelogs = None

                cnv = arocnv.ConvertGnss
                step_obj = cnv(out_dir=out_dir,
                               tmp_dir=tmp_dir,
                               log_dir=log_dir,
                               epoch_range=epo_obj_stp,
                               site=y_station['site'],
                               session=y_ses['general'],
                               metadata=sitelogs,
                               options=y_stp['options'])

            elif k_stp == 'split':
                if not _is_cfg_bloc_active(y_stp):
                    continue

                if y_station['site']['sitelog_path']:
                    sitelogs = y_station['site']['sitelog_path']
                else:
                    sitelogs = None

                spl = arohdl.SplitGnss
                step_obj = spl(out_dir=out_dir,
                               tmp_dir=tmp_dir,
                               log_dir=log_dir,
                               epoch_range=epo_obj_stp,
                               site=y_station['site'],
                               session=y_ses['general'],
                               metadata=sitelogs,
                               options=y_stp['options'])

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
    Check if a parent dictionary exists
    
    will translate it with the environment variable first
    
    internal function for read_cfg
    """
    parent_dir_out = arocmn.translator(parent_dir)

    if not os.path.isdir(parent_dir_out):
        logger.error("%s do not exists, create it first", parent_dir_out)
        raise FileNotFoundError(None, parent_dir_out + " do not exists, create it first")
    else:
        return None


def _is_cfg_bloc_active(ywkf):
    if 'active' in ywkf.keys():
        if ywkf['active']:
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
    return arocmn.EpochRange(epoch_range_dic['epoch1'],
                             epoch_range_dic['epoch2'],
                             epoch_range_dic['period'],
                             epoch_range_dic['round_method'],
                             epoch_range_dic['tz'])


def _get_dir_path(y_step,
                  dir_type='out',
                  check_parent_dir_existence=True):
    dir_parent = y_step[dir_type + '_dir_parent']
    structure = y_step[dir_type + '_structure']
    if check_parent_dir_existence:
        _check_parent_dir_existence(dir_parent)
    dir_path = os.path.join(dir_parent, structure)

    return dir_path, dir_parent, structure


def update_w_main_dic(d, u=None, specific_value='FROM_MAIN'):
    if u is None:
        return d
    for k, v in u.items():
        if not k in d.keys():
            continue
        if d[k] == specific_value:
            d[k] = v
        elif isinstance(v, collections.abc.Mapping):
            d[k] = update_w_main_dic(d.get(k, {}), v)
        else:
            if d[k] == specific_value:
                d[k] = v
    return d

