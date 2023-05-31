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

flist = []

###############################################################################
########### RAW FILES




##################
######## OVSM

nmin = 1
nmax = 10000000
nyear = 8
minyear = 2019


if  False:
    p="/net/baiededix/ovsm/ACQUI/Deformations/GPS/data" 
    regex=".*(ILAM|BIM0|SAM0|MFO0).*"
    flist = utils.find_recursive(p,regex,case_sensitive=False)
    
flist = flist[nmin:nmax]

flist = [f for f in flist if not "Rinex" in f]
flist = [f for f in flist if not "ZIP" in f]

#### OUT DIRECTORY
outdir_logs = "/scratch/convgnss/022_SONEL_conv_MQ/logs"
outdir_converted = "/scratch/convgnss/022_SONEL_conv_MQ/converted"
outdir_rinexmoded = "/scratch/convgnss/022_SONEL_conv_MQ/rinexmoded" 


##################
######## OVSG
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

    flist = utils.find_recursive(p,regex,case_sensitive=False)

flist = flist[nmin:nmax]

flist = [f for f in flist if not "Rinex" in f]
flist = [f for f in flist if not "ZIP" in f]

#### OUT DIRECTORY
outdir = "/scratch/convgnss/090_compar_IPGPTeria_GP/"
outdir_logs = outdir + "/logs"
outdir_converted =  outdir + "/converted"
outdir_rinexmoded =  outdir + "/rinexmoded" 



################### 
######## OVPF
if 0:
    p="/net/baiededix/ovpf/miroir_ovpf/DonneesAcquisition/geodesie/GPSPermanent/" 
    regex=".*(FEUG|GBNG|GBSG|HDLG|TRCG).*"

    regex=".*(BOMG|BORG|C98G|CASG|CRAG|DERG|DSRG|ENCG|ENOG|FERG|FEUG|FJAG|FOAG|FREG|GB1G|GBNG|GBSG|GITG|GLOR|GPNG|GPSG|HDLG|KNKL|MABE|MAIG|MANB|MTSB|PBRG|PMZI|PRAG|PVDG|RVAG|RVLG|SAND|SNEG|TRCG).*"

    flist = utils.find_recursive(p,regex,case_sensitive=False)
else:
    p="/home/sakic/020_TEMP/Raw_PF_mk01a.list"
    flist = open(p,"r+").readlines()


nmin = 1
nmax = 10000000
nyear = 8
minyear = 2018



flist = flist[nmin:nmax]

flist = [f.strip() for f in flist]
flist = [f for f in flist if not "Rinex" in f]
flist = [f for f in flist if not "ZIP" in f]


#### OUT DIRECTORY
outdir = "/scratch/convgnss/040_big_conv_PF/"
outdir_logs = outdir + "/logs"
outdir_converted =  outdir + "/converted"
outdir_rinexmoded =  outdir + "/rinexmoded" 





###############################################################################
########### SITELOGS
psitelogs = "/work/sitelogs/SITELOGS"
sitelogs = rinexmod_api.sitelog_input_manage(psitelogs,force=False)


ts = utils.get_timestamp()
utils.create_dir(outdir_logs)
F_raw_fail = open(os.path.join(outdir_logs,ts + "_raw_fail.log"), "a+")
F_raw_ok   = open(os.path.join(outdir_logs,ts + "_raw_ok.log"), "a+") 
F_rnx_fail = open(os.path.join(outdir_logs,ts + "_rnx_fail.log"), "a+") 
F_rnx_ok   = open(os.path.join(outdir_logs,ts + "_rnx_ok.log"), "a+") 


prev_raw_ok_logs = utils.find_recursive(outdir_logs,'*_raw_ok.log')

prev_raw_ok = list(np.hstack([open(f,"r+").readlines() for f in prev_raw_ok_logs]))
prev_raw_ok = [f.strip() for f in prev_raw_ok]

print(prev_raw_ok_logs)
print(prev_raw_ok)

for fraw in flist:    
    if fraw in prev_raw_ok:
        print(fraw,"was OK during a previous run, skip")
        continue
    
    if "Problem" in fraw:
        print(fraw,"has Problem, skip")
        continue
    
    year_folder = int(fraw.split("/")[nyear])
    #print(year_folder)
    try:
        if year_folder < minyear:
            continue
    except:
        continue
    
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
        F_raw_fail.write(str(fraw) + '\n')
        continue
    elif re.match(".TG!$",ext) or re.match(".DAT",ext) or re.match(".Z",ext):
        continue
    else:
        conve = "auto"
    
    print("converter:",conve)
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
        
        F_rnx_ok.write(str(frnxtmp) + '\n')
        F_raw_ok.write(str(fraw) + '\n')
    except:
        F_rnx_fail.write(str(frnxtmp) + '\n')
        continue
        
    
    



