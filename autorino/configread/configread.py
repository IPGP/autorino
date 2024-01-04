#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 15:47:05 2022

@author: psakicki
"""

import datetime as dt
import pandas as pd
import numpy as np
import os
from autorino import download as ardl

import yaml

def session_download_from_configfile(configfile_path):
    
    y1 = yaml.safe_load(open(configfile_path))
    
    ystat = y1["station"]

    protocol = ystat["access"]["protocol"]
    hostname = ystat["access"]["hostname"]
    sta_user = ystat["access"]["login"]
    sta_pass = ystat["access"]["password"]
    site = ystat["site"]    
    
    ysess_lst = ystat["sessions_list"]
    
    sess_stk, dwnld_stk = [], []
    
    for yses_i in ysess_lst:
        ########### session
        yses = yses_i["session"]
        name   = yses["name"]
        
        session_period = yses["file_period"]
        remote_dir     = yses["remote_dir"]
        remote_fname   = yses["remote_fname"]    
        
        sess = ardl.SessionGnss(
        name = name,
        protocol = protocol,
        remote_dir=remote_dir,
        hostname=hostname,
        sta_user=sta_user,
        sta_pass=sta_pass,
        site=site,
        session_period=session_period,
        remote_fname=remote_fname)
        
        sess_stk.append(sess)

        ##### Epoch rang
        Yepochrang = yses_i["epoch_range"]        
        rang = ardl.EpochRange(Yepochrang["epoch1"],
                               Yepochrang["epoch2"],
                               session_period)

        ############ Workflow
        Ywfl = yses_i["workflow"]
        ydwnld = Ywfl["download"]
        
        output_dir_parent = ydwnld["output_dir_parent"] 
        output_dir_struture = ydwnld["output_dir_structure"] 
        output_path = os.path.join(output_dir_parent,
                                   output_dir_struture)


        
        dwnld = ardl.DownloadGnss(sess,rang,output_path)
        
        dwnld_stk.append(dwnld)
        
    # if len(sess_stk) < 2:
        # return sess_stk[0], req_stk[0]
    # else:
    return sess_stk, dwnld_stk
