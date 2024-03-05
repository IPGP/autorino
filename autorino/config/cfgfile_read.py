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
                    main_cfg_dic={}):
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

    y_station = y["station"]

    y_site = y_station["site"]
    y_device = y_station["device"]
    y_access = y_station["access"]

    y_sessions_list = y_station["sessions_list"]

    workflow_lis = read_configfile_sessions_list(y_sessions_list,
                                                 y_site=y_site,
                                                 y_access=y_access,
                                                 main_cfg_dic=main_cfg_dic)

    return workflow_lis, y_site, y_device, y_access


def read_configfile_sessions_list(y_sessions_list_inp,
                                  epoch_range_inp=None,
                                  y_site_inp=None,
                                  y_access_inp=None,
                                  main_cfg_dic={}):
    logger.info('start to read configfile: %s', y_sessions_list_inp)
    if type(y_sessions_list_inp) is dict:
        y_sessions_list = y_sessions_list_inp
    else:  ### it is a path, a main config file
        y_main = yaml.safe_load(open(y_sessions_list_inp))
        y_sessions_list = y_main["sessions_list"]

    for yses in y_sessions_list:
        ##### TMP DIRECTORY
        tmp_dir, _, _ = _get_dir_path('session', yses,'tmp', main_cfg_dic)

        ##### LOG DIRECTORY
        log_dir, _, _ = _get_dir_path('session',yses,'tmp', main_cfg_dic)


        ##### EPOCH RANGE AT THE SESSION LEVEL
        if not epoch_range_inp:
            epo_obj_use = _epoch_range_from_cfg_bloc(yses['epoch_range'])
        else:
            epo_obj_use = epoch_range_inp

        workflow_lis = []
        workflow_dic = {}

        #### manage workflow
        y_workflow = yses['workflow']
        main_cfg_dic_workflow = main_cfg_dic['workflow']

        for k_step, y_step in y_workflow.items():

            out_dir, _, _ = _get_dir_path(k_step, y_step, 'out',
                                          main_cfg_dic['workflow'])

            inp_dir, inp_dir_parent, inp_structure = _get_dir_path(k_step, y_step, 'inp',
                                                                   main_cfg_dic['workflow'])
            if k_step == 'download':
                if not _is_cfg_bloc_active(y_step):
                    continue

                dwl = arodwl.DownloadGnss
                step_obj = dwl(out_dir=out_dir,
                               tmp_dir=tmp_dir,
                               log_dir=log_dir,
                               epoch_range=epo_obj_use,
                               access=y_access_inp,
                               remote_dir=inp_dir_parent,
                               remote_fname=inp_structure,
                               site=y_site_inp,
                               session=yses['session'])

            # appended in lis and dic at the end of the tests

            elif k_step == 'conversion':
                if not _is_cfg_bloc_active(y_step):
                    continue

                if y_site_inp and y_site_inp['sitelog_path']:
                    sitelogs = y_site_inp['sitelog_path']
                else:
                    sitelogs = None

                cnv = arocnv.ConvertGnss
                step_obj = cnv(out_dir=out_dir,
                               tmp_dir=tmp_dir,
                               log_dir=log_dir,
                               epoch_range=epo_obj_use,
                               site=y_site_inp,
                               session=yses['session'],
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


def _get_dir_path(k_step,
                  y_step,
                  dir_type='out',
                  main_default_step_dic={}):

    if k_step in main_default_step_dic.keys():
        dir_parent = main_default_step_dic[k_step][dir_type + '_dir_parent']
        structure = main_default_step_dic[k_step][dir_type + '_structure']
    else:
        dir_parent = y_step[dir_type + '_dir_parent']
        structure = y_step[dir_type + '_structure']

    _check_parent_dir_existence(dir_parent)
    dir_path = os.path.join(dir_parent, structure)

    return dir_path, dir_parent, structure
