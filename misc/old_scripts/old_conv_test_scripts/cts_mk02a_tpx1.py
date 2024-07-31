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

import os

import converters as cv
import rinexmod_api

from geodezyx import utils

p="/net/baiededix/ovpf/miroir_ovpf/DonneesAcquisition/geodesie/GPSPermanent/2023" 
p="/home/psakicki/GFZ_WORK/IPGP_WORK/OVS/GNSS_OVS/0010_work_area/2202_DataExemple/binex_mtq"

psitelogs="/home/psakicki/GFZ_WORK/IPGP_WORK/OVS/GNSS_OVS/0030_sites_manage_n_M3G/0020_sitelogs/030_sitelogs_M3G/2205_automatic_download"

outdir_converted = "/home/psakicki/aaa_FOURBI/convertertest/"
outdir_rinexmoded = "/home/psakicki/aaa_FOURBI/convertertest/converted/rinexmoded" 
utils.create_dir(outdir_rinexmoded)
utils.create_dir(outdir_converted)

conv_cmd_build_convbin=1
conv_cmd_build_tps2rin=0

verbose = True

sitelogs = rinexmod_api.metadata_input_manage(psitelogs, force=False)
sitelog_bim0 = rinexmod_api.sitelog_find_site("bim0", sitelogs,force=False)

#### TRIMBLE
if conv_cmd_build_convbin:
    for fraw in utils.find_recursive(p,"*BNX"):
        frnxtmp, _ = cv.converter_run(fraw, outdir_converted,
                                      converter = 'auto')
        
        try:
            rinexmod_api.rinexmod(frnxtmp,outdir_rinexmoded,
                                  marker=os.path.basename(fraw)[1:5],
                                  sitelog=sitelogs,
                                  force_rnx_load=True,
                                  force_sitelog=True,
                                  verbose=verbose)
        except:
            continue

p = "/home/psakicki/GFZ_WORK/IPGP_WORK/OVS/GNSS_OVS/0010_work_area/2202_DataExemple/tps_glp/"
if conv_cmd_build_tps2rin:
    for fraw in utils.find_recursive(p,"*TPS"):
        frnxtmp, _ = cv.converter_run(fraw, outdir_converted,
                                      converter = 'tps2rin')
        rinexmod_api.rinexmod(frnxtmp,outdir_rinexmoded,
                              #marker=os.path.basename(fraw)[1:5],
                              sitelog=sitelogs,
                              force_rnx_load=True,
                              force_sitelog=True,
                              verbose=verbose)


P = "/home/psakicki/aaa_FOURBI/convertertest/dhs03020.11p"
RNX = rinexmod_api.RinexFile(P,False)
