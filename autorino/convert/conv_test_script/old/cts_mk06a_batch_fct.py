#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  8 18:45:58 2023

@author: psakicki
"""

#### Import star style
#from geodezyx import *                   # Import the GeodeZYX modules
#from geodezyx.externlib import *         # Import the external modules
#from geodezyx.megalib.megalib import *   # Import the legacy modules names

from geodezyx import utils
import autorino.convert.converters as cv
import rinexmod_api
from pathlib import Path
import os
import re 
import numpy as np
import datetime as dt
import dateutil

def _filter_prev_raw_ok_or_exclu(flist,prev_raw_ok,
                                 message_manu_exclu=False):
    flist_out = []
    for f in flist:
        if f in prev_raw_ok:
            if not message_manu_exclu:
                print(f,"was OK during a previous run, skipped")
            else:
                print(f,"was manually excluded in the exclusion list, skipped")
                
        else:
            flist_out.append(f)
    return flist_out


def _filter_bad_keywords(flist,keywords_path_excl):
    flist_out = []
    for f in flist:
        boolbad = utils.patterns_in_string_checker(f,*keywords_path_excl)
        if boolbad:
            print(f," contains an excluded keyword, skipped")
        else:
            flist_out.append(f)
    return flist_out
            
            
def _filter_year_min_max(flist,year_in_inp_path,year_min_max):
    flist_out = []
    for f in flist:
        year_folder = int(f.split("/")[year_in_inp_path])
        if year_folder < year_min_max[0] or year_folder > year_min_max[1]:
            print(f,"not in year range, skipped")
        else:
            flist_out.append(f)
    return flist_out 

  

def _input_files_reader(inp_fil,inp_regex=".*"):
    if not inp_fil:
        flist  = []
    elif type(inp_fil) is tuple and os.path.isfile(inp_fil[0]):
        flist = list(np.hstack([open(f,"r+").readlines() for f in inp_fil]))
        flist = [f.strip() for f in flist]
    elif type(inp_fil) is list:
        flist = inp_fil
    elif os.path.isfile(inp_fil):
        flist = open(inp_fil,"r+").readlines()
        flist = [f.strip() for f in flist]
    elif os.path.isdir(inp_fil):
        flist = utils.find_recursive(inp_fil,
                                     inp_regex,
                                     case_sensitive=False)
    else:
        flist = []
        logger.warning("the filelist is empty") 
        
    return flist


import docker

def stop_long_running_containers(max_running_time=120):
    client = docker.from_env()
    containers = client.containers.list()

    for container in containers:
        ### Calculate the time elapsed since the container was started
        #created_at = container.attrs['Created']
        started_at = container.attrs['State']['StartedAt']
        
        started_at =  dateutil.parser.parse(started_at)
        elapsed_time = dt.datetime.now(dt.timezone.utc) - started_at
        
        if elapsed_time > dt.timedelta(seconds=max_running_time):
            container.stop()
            print(f'Stopped container {container.name} after {elapsed_time} seconds.')
            
    return None


def converter_batch(input_files,
                    outdir,
                    inp_regex=".*",
                    sitelogs_inp=None,
                    year_in_inp_path=None,
                    year_min_max=(1980,2099),
                    files_idx_minmax=(None,None),
                    keywords_path_excl=['Problem','Rinex','ZIP'],
                    raw_excl_list=None):
    
    
    ###############################################
    ### read input lists or regex
    flist = _input_files_reader(input_files,inp_regex)
    

    ###############################################
    ### read sitelogs        
    if os.path.isdir(sitelogs_inp):
        sitelogs = rinexmod_api.sitelog_input_manage(sitelogs_inp,
                                                     force=False)
    
    ###############################################
    ### def output folders
    outdir_logs = outdir + "/logs"
    outdir_converted =  outdir + "/converted"
    outdir_rinexmoded =  outdir + "/rinexmoded" 

    utils.create_dir(outdir_logs)
    
    ##############################################
    ### def output logs
    ts = utils.get_timestamp()
    log_raw_fail = os.path.join(outdir_logs,ts + "_raw_fail.log")
    log_raw_ok   = os.path.join(outdir_logs,ts + "_raw_ok.log")
    log_rnx_fail = os.path.join(outdir_logs,ts + "_rnx_fail.log")
    log_rnx_ok   = os.path.join(outdir_logs,ts + "_rnx_ok.log")

    ##############################################
    ### previous OK files
    prev_raw_ok_logs = utils.find_recursive(outdir_logs,'*_raw_ok.log')    
    prev_raw_ok = _input_files_reader(tuple(prev_raw_ok_logs))

    ##############################################
    ### previous exclu files
    prev_raw_exclu = _input_files_reader(raw_excl_list)
    
    ##############################################
    ### filtering
    flist = _filter_year_min_max(flist, year_in_inp_path, year_min_max)
    flist = _filter_prev_raw_ok_or_exclu(flist, prev_raw_ok,False)
    flist = _filter_prev_raw_ok_or_exclu(flist, prev_raw_exclu,True)
    flist = _filter_bad_keywords(flist, keywords_path_excl)

    for fraw in flist:    

        fraw = Path(fraw)
        ext = fraw.suffix.upper()
        if re.match(".BNX",ext):
            site = fraw.name[1:5]
        else:
            site = fraw.name[:4]
    
        outdir_rinexmoded_use = os.path.join(outdir_rinexmoded,site.upper())
        utils.create_dir(outdir_converted)
        utils.create_dir(outdir_rinexmoded_use)
    
        print("ext",ext)
        
        if not ext:
            conve = "tps2rin"
        elif re.match("^.[0-9]{3}$",ext):
            utils.write_in_file(str(fraw), log_raw_fail, append=True)
            continue
        elif re.match(".TG!$",ext) or re.match(".DAT",ext) or re.match(".Z",ext):
            continue
        else:
            conve = "auto"
        
        print("converter:",conve)
        
        #os.system("docker stop $(docker ps -a -q)")        
        stop_long_running_containers()
        
        frnxtmp, _ = cv.converter_run(fraw,
                                      outdir_converted,
                                      converter = conve)
        try:
            rinexmod_api.rinexmod(frnxtmp,
                                  outdir_rinexmoded_use,
                                  marker=site,
                                  compression="gz",
                                  longname=True,
                                  sitelog=sitelogs,
                                  force_rnx_load=True,
                                  verbose=True,
                                  full_history=True)
            
            utils.write_in_file(str(frnxtmp), log_rnx_ok,append=True)
            utils.write_in_file(str(fraw), log_raw_ok,append=True)
        except:
            utils.write_in_file(str(frnxtmp), log_rnx_fail,append=True)
            continue

#####################################################################################################
#####################################################################################################
#####################################################################################################











    
###################### OVPF
if 0:
    p="/net/baiededix/ovpf/miroir_ovpf/DonneesAcquisition/geodesie/GPSPermanent/" 
    regex=".*(FEUG|GBNG|GBSG|HDLG|TRCG).*"

    regex=".*(BOMG|BORG|C98G|CASG|CRAG|DERG|DSRG|ENCG|ENOG|FERG|FEUG|FJAG|FOAG|FREG|GB1G|GBNG|GBSG|GITG|GLOR|GPNG|GPSG|HDLG|KNKL|MABE|MAIG|MANB|MTSB|PBRG|PMZI|PRAG|PVDG|RVAG|RVLG|SAND|SNEG|TRCG).*"

    flist = utils.find_recursive(p,regex,case_sensitive=False)
else:
    p="/home/sakic/020_TEMP/Raw_PF_mk01a.list"

nyear = 8
minyear = 2019

#### OUT DIRECTORY
outdir = "/scratch/convgnss/040_big_conv_PF/"
psitelogs = "/work/sitelogs/SITELOGS"
keywords_path_excl=['Problem','Rinex','ZIP',"MAIG"]
    
######################### OVSG
nmin = 1
nmax = 10000000
nyear = 7
minyear = 2020

if True:
    p="/net/baiededix/ovsg/acqui/GPSOVSG/raw/" 
    # pour Mederic
    regex=".*(TDB0|MGL0|DHS0|CBE0|ADE0|DSD0|DHS0).*"

    #compar Teria
    regex=".*(HOUE).*"
    regex=".*(ABD0|CBE0|HOUE).*"
    regex=".*(ABD0).*"


#### OUT DIRECTORY
outdir = "/scratch/convgnss/090_compar_IPGPTeria_GP/"
psitelogs = "/work/sitelogs/SITELOGS"
keywords_path_excl=['Problem','Rinex','ZIP',"MAIG"]

##################################################################


converter_batch(p, 
                outdir,
                inp_regex=regex,
                year_in_inp_path=nyear,
                year_min_max=(minyear,2099),
                keywords_path_excl=keywords_path_excl,
                sitelogs_inp=psitelogs)
    