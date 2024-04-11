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
import autorino.convert.conv_cmd_run as cv
import rinexmod_api
from pathlib import Path
import os
import re 



########### RAW FILES 
#### OVPF
p="/net/baiededix/ovpf/miroir_ovpf/DonneesAcquisition/geodesie/GPSPermanent/" 
regex=".*(FEUG|GBNG|GB1G|TRCG|HDLG|GBSG).*"

nmin = 1
nmax = 10000000

flist = utils.find_recursive(p,regex,case_sensitive=False)
flist = flist[nmin:nmax]

flist = [f for f in flist if not "Rinex" in f]
flist = [f for f in flist if not "ZIP" in f]


########### SITELOGS
psitelogs = "/work/sitelogs/SITELOGS"
sitelogs = rinexmod_api.sitelog_input_manage(psitelogs,force=False)


########### OUT DIRECTORY
outdir_converted = "/scratch/convgnss/020_SONEL_conv/converted"
outdir_rinexmoded = "/scratch/convgnss/020_SONEL_conv/rinexmoded" 

for fraw in flist:   
    fraw = Path(fraw)
    ext = fraw.suffix.upper()
    site = fraw.name[:4]
    
    
    utils.create_dir(outdir_converted)
    outdir_rinexmoded_use = os.path.join(outdir_rinexmoded,"TOTO")
    utils.create_dir(outdir_rinexmoded_use)
    
    print("ext",ext)
    
    if not ext:
        conve = "tps2rin"
    elif re.match("^.[0-9]{3}$",ext):
        continue
    else:
        conve = "auto"
    
    print("coverter:",conve)
    frnxtmp, _ = cv.converter_run(fraw,
                                  outdir_converted,
                                  converter = conve)
    
    
    try:
        rinexmod_api.rinexmod(frnxtmp,
                              outdir_rinexmoded_use,
                              sitelog=sitelogs,
                              force_rnx_load=True,
                              verbose=True,
                              full_history=True)
    except:
        continue
        
    
    



