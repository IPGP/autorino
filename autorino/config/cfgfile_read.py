#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 15:47:05 2022

@author: psakicki
"""

import os
import autorino.common as arocmn
import autorino.download as arodwl
import autorino.convert as arocnv

#import autorino.session as aroses
#import autorino.epochrange as aroepo

import yaml
import glob
import mergedeep

# Create a logger object.
import logging

logger = logging.getLogger(__name__)


def autorino_run(cfg_in):
    if os.path.isdir(cfg_in):
        cfg_use_lis = glob.glob(cfg_in + '/*yml')
    elif os.path.isfile(cfg_in):
        cfg_use_lis = [cfg_in]
    else:
        logger.error("%s does not exist, check input config file/dir", cfg_in)
        raise Exception

    for cfg_use in cfg_use_lis:
        workflow_lis, y_site, y_device, y_access = read_configfile(cfg_use)
        run_workflow(workflow_lis)

    return None


def run_workflow(workflow_lis, print_table=True):
    wkf_prev = None
    for iwkf, wkf in enumerate(workflow_lis):
        if iwkf > 0:
            wkf_prev = workflow_lis[iwkf - 1]

        if wkf.get_step_type() == "DownloadGnss":
            wkf.download(print_table)
        elif wkf.get_step_type() == "ConvertGnss":
            wkf.load_table_from_prev_step_table(wkf_prev.table)
            wkf.convert_table(print_table)


def read_configfile(configfile_path,
                    epoch_range_inp=None,
                    main_cfg_path=None):
    """
    Load a config file (YAML format) and 
    return a "Workflow list" i.e. a list of StepGnss object 
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
    workflow_lis : list
        "Workflow list" i.e. a list of StepGnss object 
        to be launched sequentially.
    y_site : dict
        site dictionary.
    y_device : dict
        device dictionary.
    y_access : dict
        station access dictionary.
    """
    logger.info('start to read configfile: %s', configfile_path)
    y = yaml.safe_load(open(configfile_path))

    if main_cfg_path:
        ymain = yaml.safe_load(open(main_cfg_path))
        ymain_sessions = ymain['sessions']
    else:
        ymain_sessions = None

    y_station = y["station"]
    y_site = y_station["site"]
    y_device = y_station["device"]
    y_access = y_station["access"]
    y_sessions = y_station["sessions"]

    workflow_lis, workflow_dic = read_configfile_sessions_dict(y_sessions,
                                                               y_site=y_site,
                                                               y_access=y_access,
                                                               epoch_range_inp=None,
                                                               y_main_sessions_dic=ymain_sessions)

    return workflow_lis, workflow_dic, y_site, y_device, y_access


def read_configfile_sessions_dict(y_sessions_dict,
                                  epoch_range=None,
                                  y_site=None,
                                  y_access=None,
                                  epoch_range_inp=None,
                                  y_main_sessions_dic=None):

    for kses, yses in y_sessions_dict.items():

        yses_main = y_main_sessions_dic[kses]

        ygen = yses['general']
        session_name = ygen['name']

        ygen_main = yses_main['general']

        ygen = update_dic_deep(ygen,ygen_main)

        ##### TMP DIRECTORY
        tmp_dir, _, _ = _get_dir_path(ygen, 'tmp')

        ##### LOG DIRECTORY
        log_dir, _, _ = _get_dir_path(ygen, 'log')

        ##### EPOCH RANGE AT THE SESSION LEVEL
        if not epoch_range_inp:
            epo_obj_use = _epoch_range_from_cfg_bloc(yses['epoch_range'])
        else:
            epo_obj_use = epoch_range_inp

        workflow_lis = []
        workflow_dic = {}

        #### manage workflow
        y_workflow = yses['workflow']
        y_workflow_main = yses_main['workflow']


        for k_step, y_step in y_workflow.items():

            y_step_main = y_workflow_main[k_step]
            y_step = update_dic_deep(y_step, y_step_main)

            out_dir, _, _ = _get_dir_path(y_step, 'out')
            inp_dir, inp_dir_parent, inp_structure = _get_dir_path(y_step, 'inp',
                                                                   check_parent_dir_existence=False)

            if k_step == 'download':
                if not _is_cfg_bloc_active(y_step):
                    continue

                dwl = arodwl.DownloadGnss
                step_obj = dwl(out_dir=out_dir,
                               tmp_dir=tmp_dir,
                               log_dir=log_dir,
                               epoch_range=epo_obj_use,
                               access=y_access,
                               remote_dir=inp_dir_parent,
                               remote_fname=inp_structure,
                               site=y_site,
                               session=yses['general'])

            # appended in lis and dic at the end of the tests

            elif k_step == 'conversion':
                if not _is_cfg_bloc_active(y_step):
                    continue

                if y_site and y_site['sitelog_path']:
                    sitelogs = y_site['sitelog_path']
                else:
                    sitelogs = None

                cnv = arocnv.ConvertGnss
                step_obj = cnv(out_dir=out_dir,
                               tmp_dir=tmp_dir,
                               log_dir=log_dir,
                               epoch_range=epo_obj_use,
                               site=y_site,
                               session=yses['general'],
                               sitelogs=sitelogs)

                # appended in lis and dic at the end of the tests

            else:
                logger.warning("unknown step %s in config file, skipped...")
                continue

            workflow_lis.append(step_obj)
            workflow_dic[k_step] = step_obj

    return workflow_lis, workflow_dic


def _check_parent_dir_existence(parent_dir_inp):
    """
    Check if a parent dictionary exists
    
    will translate it with the environment variable first
    
    internal function for read_configfile
    """
    parent_dir_out = arocmn.translator(parent_dir_inp)

    if not os.path.isdir(parent_dir_out):
        logger.error("%s do not exists, create it first", parent_dir_out)
        raise FileNotFoundError(None, parent_dir_out + " do not exists, create it first")
    else:
        return None


def _is_cfg_bloc_active(ywkf_inp):
    if 'active' in ywkf_inp.keys():
        if ywkf_inp['active']:
            return True
        else:
            return False
    else:  ### if no 'active' key, we assume the bloc active
        return True


def _epoch_range_from_cfg_bloc(epoch_range_dic):
    """
    get an EpochRange object from epoch_range dictionary bloc
    internal function for read_configfile

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

import collections.abc

def update_dic_deep(d, u, specific_key='FROM_MAIN'):
    dout = d.copy()
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            dout[k] = update_dic_deep(dout.get(k, {}), v)
        else:
            if not (specific_key and k == specific_key):
                continue
            else:
                dout[k] = v
    return dout