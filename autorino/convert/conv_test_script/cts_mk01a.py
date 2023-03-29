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

p="/net/baiededix/ovpf/miroir_ovpf/DonneesAcquisition/geodesie/GPSPermanent/" 
psitelogs = "/work/sitelogs/SITELOGS"
outdir_converted = "/scratch/convgnss/010_tests_autorino_converters/converted"
outdir_rinexmoded = "/scratch/convgnss/010_tests_autorino_converters/rinexmoded" 
utils.create_dir(outdir_rinexmoded)
utils.create_dir(outdir_converted)

conv_trm2rinex=1 
conv_trm_runpkr00=0
conv_trm_teqc=0
conv_leica_mdb2rinex=0
conv_sept_sbf2rin=0
verbose=False

nmax = 10

sitelogs = rinexmod_api.sitelog_input_manage(psitelogs,force=False)

regex_trm2rinex=".*(FEUG|GBNG|GB1G|TRCG|HDLG|GBSG).*T02"


#### TRIMBLE
if conv_trm2rinex:
    flist = utils.find_recursive(p,regex_trm2rinex,case_sensitive=False)
    flist = flist[:nmax]
    for fraw in flist:
        frnxtmp, _ = cv.converter_run(fraw, outdir_converted, converter = 'trm2rinex')
        rinexmod_api.rinexmod(frnxtmp,outdir_rinexmoded,sitelog=sitelogs,force_rnx_load=True,verbose=verbose,full_history=True)

#### TRIMBLE RUNPKR00
if conv_trm_runpkr00:
    flist = utils.find_recursive(p,"*T02")
    flist = flist[:nmax]
    for fraw in flist:
        cv.converter_run(fraw, outdir_converted, converter = 'runpkr00')
        rinexmod_api.rinexmod(frnxtmp,outdir_rinexmoded,sitelog=sitelogs,force_rnx_load=True,verbose=verbose)

#### TRIMBLE TEQC
if conv_trm_teqc:
    flist = utils.find_recursive(outdir_converted,"*tgd")
    flist = flist[:nmax]
    for fraw in flist:
        frnxtmp, _ = cv.converter_run(fraw, outdir_converted, converter = 'teqc')
        rinexmod_api.rinexmod(frnxtmp,outdir_rinexmoded,sitelog=sitelogs,force_rnx_load=True,verbose=verbose)

#### MDB2RINEX
if conv_leica_mdb2rinex:
    flist = utils.find_recursive(p,"*m00")
    flist = flist[:nmax]
    for fraw in flist:
        frnxtmp, _ = cv.converter_run(fraw, outdir_converted, converter = 'mdb2rinex')
        rinexmod_api.rinexmod(frnxtmp,outdir_rinexmoded,sitelog=sitelogs,force_rnx_load=True,verbose=verbose)

#### SBF2RIN
if conv_sept_sbf2rin:
    flist = utils.find_recursive(p,"*_")
    flist = flist[:nmax]
    for fraw in flist:
        frnxtmp, _ = cv.converter_run(fraw, outdir_converted, converter = 'sbf2rin')    
        rinexmod_api.rinexmod(frnxtmp,outdir_rinexmoded,sitelog=sitelogs,force_rnx_load=True,verbose=verbose)


for frnx in utils.find_recursive(outdir_converted,"*rnx*"):
    RNX = rinexmod_api.RinexFile(frnx,True)





