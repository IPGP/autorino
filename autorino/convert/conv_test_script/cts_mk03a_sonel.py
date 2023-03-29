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
import converters as cv
import rinexmod_api
import os



########### RAW FILES 
#### OVPF
p="/net/baiededix/ovpf/miroir_ovpf/DonneesAcquisition/geodesie/GPSPermanent/" 
regex=".*(FEUG|GBNG|GB1G|TRCG|HDLG|GBSG).*"

nmax = 10000000

flist = utils.find_recursive(p,regex,case_sensitive=False)
flist = flist[:nmax]

########### SITELOGS
psitelogs = "/work/sitelogs/SITELOGS"
sitelogs = rinexmod_api.sitelog_input_manage(psitelogs,force=False)


########### OUT DIRECTORY
outdir_converted = "/scratch/convgnss/020_SONEL_conv/converted"
outdir_rinexmoded = "/scratch/convgnss/020_SONEL_conv/rinexmoded" 

for fraw in flist:
    utils.create_dir(outdir_rinexmoded)
    outdir_rinexmoded_use = os.path.join(outdir_rinexmoded,"TOTO")
    utils.create_dir(outdir_converted)
    
    frnxtmp, _ = cv.converter_run(fraw,
                                  outdir_converted,
                                  converter = 'auto')
    
    
    rinexmod_api.rinexmod(frnxtmp,
                          outdir_rinexmoded,
                          sitelog=sitelogs,
                          force_rnx_load=True,
                          verbose=True,
                          full_history=True)





