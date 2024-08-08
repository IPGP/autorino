#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  7 14:27:21 2023

@author: psakicki
"""

import autorino.convert.cnv_batch as cvb

#### Import star style
from geodezyx import *  # Import the GeodeZYX modules

###################### OVSM for SONEL
psitelogs = "/work/metadata/SITELOGS"


#p="/net/baiededix/ovsm/ACQUI/Deformations/GPS/data" 
#regex=".*(ILAM|BIM0|SAM0|MFO0).*"
regex=".*"
keywords_path_excl=[]


########## 2022 process 
flist = "/home/sakic/020_TEMP/Raw_sonel_MQ_mk01a.list"
outdir = "/scratch/convgnss/022_SONEL_conv_MQ"
nyear = 8
minyear = 2018
maxyear = 2023


outdir = "/scratch/convgnss/031_test_firmware_SAM0"
regex=".*SAM.*"
nyear = 8
minyear = 2020
maxyear = 2023


##################################################################
raw_excl_list = tuple(utils.find_recursive(outdir,'*_rnx_fail.log'))

cvb.converter_batch(flist, 
                    outdir,
                    inp_regex=regex,
                    year_in_inp_path=nyear,
                    year_min_max=(minyear,maxyear),
                    keywords_path_excl=keywords_path_excl,
                    sitelogs_inp=psitelogs,
                    raw_excl_list=raw_excl_list)
