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
        
        _check_parent_dir_existence(yses['tmp_dir_parent'])
        tmp_dir = os.path.join(yses['session']['tmp_dir_parent'],
                               yses['session']['tmp_dir_structure'])

        _check_parent_dir_existence(yses['log_dir_parent'])
        log_dir = os.path.join(yses['session']['log_dir_parent'],
                               yses['session']['log_dir_structure'])
        
    
        epo_obj_gen = arogen.EpochRange(yses['epoch_range']['epoch1'], 
                                        yses['epoch_range']['epoch2'],
                                        yses['epoch_range']['period'],
                                        yses['epoch_range']['round_method'],
                                        yses['epoch_range']['tz'])
        
        workflow_lis = []
        #### manage workflow
        y_workflow =  yses['workflow']    
        for k_step, ywkf in y_workflow.items():
                    
            _check_parent_dir_existence(ywkf['out_dir_parent'])
            out_dir = os.path.join(ywkf['out_dir_parent'],
                                   ywkf['out_dir_structure'])
            
            if k_step == 'download':
                Dwl =  arodwl.DownloadGnss
                dwl_obj = Dwl(out_dir=out_dir,
                              tmp_dir=tmp_dir,
                              log_dir=log_dir,
                              epoch_range=epo_obj_gen,
                              access=y_access,
                              remote_dir=ywkf['remote_dir'],
                              remote_fname=ywkf['remote_fname'],
                              site=y_site,
                              session=yses['session'])
                
                workflow_lis.append(dwl_obj)
                
            if k_step == 'conversion':
                Cnv = arocnv.ConvertRinexModGnss
                cnv_obj = Cnv(out_dir=out_dir,
                              tmp_dir=tmp_dir,
                              log_dir=log_dir,
                              epoch_range=epo_obj_gen,
                              site=y_site,
                              session=yses['session'])
                
                workflow_lis.append(cnv_obj)
                
                
    return workflow_lis, y_site, y_device, y_access
                
    
def _check_parent_dir_existence(parent_dir_inp):
    """
    will translate it with the environnement variable first

    """
    parent_dir_out = arogen.translator(parent_dir_inp)
    
    if  not os.path.isdir(parent_dir_out):
        logger.error("%s do not exists, create it first")
        raise Exception
    else:
        return None
###################### FUNCTION GRAVEYARD



# def session_download_from_configfile(configfile_path):
    
#     y1 = yaml.safe_load(open(configfile_path))
    
#     ystat = y1["station"]

#     protocol = ystat["access"]["protocol"]
#     hostname = ystat["access"]["hostname"]
#     sta_user = ystat["access"]["login"]
#     sta_pass = ystat["access"]["password"]
#     site = ystat["site"]    
    
#     ysess_lst = ystat["sessions_list"]
    
#     sess_stk, dwnld_stk = [], []
    
#     for yses_i in ysess_lst:
#         ########### session
#         yses = yses_i["session"]
#         name = yses["name"]
        
#         session_period = yses["file_period"]
#         remote_dir = yses["remote_dir"]
#         tmp_dir = yses["tmp_dir"]
#         remote_fname = yses["remote_fname"]    
        
#         sess = arogen.SessionGnss(name = name,
#                                   protocol = protocol,
#                                   remote_dir=remote_dir,
#                                   tmp_dir=tmp_dir,
#                                   hostname=hostname,
#                                   sta_user=sta_user,
#                                   sta_pass=sta_pass,
#                                   site=site,
#                                   session_period=session_period,
#                                   remote_fname=remote_fname)
        
#         sess_stk.append(sess)

#         ##### Epoch rang
#         Yepochrang = yses_i["epoch_range"]        
#         rang = arogen.EpochRange(Yepochrang["epoch1"],
#                                  Yepochrang["epoch2"],
#                                  session_period)

#         ############ Workflow
#         ##### Download
#         Ywfl = yses_i["workflow"]
#         ydwnld = Ywfl["download"]
        
#         output_dir_parent = ydwnld["output_dir_parent"] 
#         output_dir_struture = ydwnld["output_dir_structure"] 
#         output_path = os.path.join(output_dir_parent,
#                                    output_dir_struture)
       
#         dwnld = arodwl.DownloadGnss(sess,rang,output_path)
        
#         dwnld_stk.append(dwnld)
        
#     # if len(sess_stk) < 2:
#         # return sess_stk[0], req_stk[0]
#     # else:
#     return sess_stk, dwnld_stk
