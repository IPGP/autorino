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
from autorino import configread as arcfg

import yaml

def session_request_from_configfile(configfile_path):
    
    Y1 = yaml.safe_load(open(configfile_path))
    
    Ystation = Y1["station"]

    protocol = Ystation["access"]["protocol"]
    hostname = Ystation["access"]["hostname"]
    sta_user = Ystation["access"]["login"]
    sta_pass = Ystation["access"]["password"]
    site = Ystation["site"]    
    
    Ysession_list = Ystation["sessions_list"]
    
    Sess_stk, Req_stk = [], []
    
    for Yses0 in Ysession_list:
        ########### Session
        Yses = Yses0["session"]
        name   = Yses["name"]
        
        session_period = Yses["file_period"]
        remote_dir     = Yses["remote_dir"]
        remote_fname   = Yses["remote_fname"]    
        
        Sess = ardl.SessionGnss(
        name = name,
        protocol = protocol,
        remote_dir=remote_dir,
        hostname=hostname,
        sta_user=sta_user,
        sta_pass=sta_pass,
        site=site,
        session_period=session_period,
        remote_fname=remote_fname)
        
        Sess_stk.append(Sess)
        
        ############ Request
        Yreq = Yses0["request"]
        Ydownload = Yreq["download"]
        
        output_dir_parent = Ydownload["output_dir_parent"] 
        output_dir_struture = Ydownload["output_dir_structure"] 
        output_path = os.path.join(output_dir_parent,
                                   output_dir_struture)

        ##### Epoch Range
        Yepochrange = Ydownload["epoch_range"]        
        Range = ardl.EpochRange(Yepochrange["epoch1"],
                                Yepochrange["epoch2"],
                                session_period)
        
        Req = ardl.DownloadGnss(Sess,Range,output_path)
        
        Req_stk.append(Req)
        
    if len(Sess_stk) < 2:
        return Sess_stk[0], Req_stk[0]
    else:
        return Sess_stk, Req_stk
