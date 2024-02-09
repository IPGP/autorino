#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 15:47:05 2022

@author: psakicki
"""

import os
import autorino.general as arogen
import autorino.download as arodwl
import autorino.convert as arocnv

#import autorino.session as aroses
#import autorino.epochrange as aroepo

import yaml

# Create a logger object.
import logging
logger = logging.getLogger(__name__)


def read_configfile(configfile_path):
    y = yaml.safe_load(open(configfile_path))
    
    y_station = y["station"]
    
    y_site = y_station["site"]
    y_device = y_station["device"]
    y_access = y_station["access"]
    
    y_sessions_list = y_station["sessions_list"]
    
    for yses in y_sessions_list:

        ##### TMP DIRECTORY
        _check_parent_dir_existence(yses['session']['tmp_dir_parent'])
        tmp_dir = os.path.join(yses['session']['tmp_dir_parent'],
                               yses['session']['tmp_dir_structure'])

        ##### LOG DIRECTORY
        _check_parent_dir_existence(yses['session']['log_dir_parent'])
        log_dir = os.path.join(yses['session']['log_dir_parent'],
                               yses['session']['log_dir_structure'])
    
        ##### EPOCH RANGE AT THE SESSION LEVEL
        epo_obj_gen = _epoch_range_from_cfg_bloc(yses['epoch_range'])
        
        workflow_lis = []
        #### manage workflow
        y_workflow =  yses['workflow']    
        for k_step, ywkf in y_workflow.items():
                    
            _check_parent_dir_existence(ywkf['out_dir_parent'])
            out_dir = os.path.join(ywkf['out_dir_parent'],
                                   ywkf['out_dir_structure'])
            
            if k_step == 'download' and ywkf['active'] == True:
                Dwl =  arodwl.DownloadGnss
                dwl_obj = Dwl(out_dir=out_dir,
                              tmp_dir=tmp_dir,
                              log_dir=log_dir,
                              epoch_range=epo_obj_gen,
                              access=y_access,
                              remote_dir=ywkf['inp_dir_parent'],
                              remote_fname=ywkf['inp_fname_structure'],
                              site=y_site,
                              session=yses['session'])
                
                workflow_lis.append(dwl_obj)
                
            if k_step == 'conversion_rinex_header_mod' and ywkf['active'] == True:
                Cnv = arocnv.ConvertRinexModGnss
                
                if y_site['sitelog_path']:
                    sitelogs=y_site['sitelog_path']
                else:
                    sitelogs=None
                
                cnv_obj = Cnv(out_dir=out_dir,
                              tmp_dir=tmp_dir,
                              log_dir=log_dir,
                              epoch_range=epo_obj_gen,
                              site=y_site,
                              session=yses['session'],
                              sitelogs=sitelogs)
                
                workflow_lis.append(cnv_obj)
                
                
    return workflow_lis, y_site, y_device, y_access
                
    
def _check_parent_dir_existence(parent_dir_inp):
    """
    will translate it with the environnement variable first

    """
    parent_dir_out = arogen.translator(parent_dir_inp)
    
    if  not os.path.isdir(parent_dir_out):
        logger.error("%s do not exists, create it first",parent_dir_out)
        raise Exception
    else:
        return None


def _epoch_range_from_cfg_bloc(epoch_range_dic):
    return arogen.EpochRange(epoch_range_dic['epoch1'], 
                             epoch_range_dic['epoch2'],
                             epoch_range_dic['period'],
                             epoch_range_dic['round_method'],
                             epoch_range_dic['tz'])
    