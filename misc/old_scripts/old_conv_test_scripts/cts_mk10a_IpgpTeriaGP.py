#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  7 14:27:01 2023

@author: psakicki
"""

#### Import star style

import autorino.convert.conv_batch as cvb




######################### OVSG Teria
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
psitelogs = "/work/metadata/SITELOGS"
keywords_path_excl=['Problem','Rinex','ZIP']

##################################################################


cvb.converter_batch(p, 
                    outdir,
                    inp_regex=regex,
                    year_in_inp_path=nyear,
                    year_min_max=(minyear,2099),
                    keywords_path_excl=keywords_path_excl,
                    sitelogs_inp=psitelogs)
    