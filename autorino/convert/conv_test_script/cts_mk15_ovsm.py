#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  7 14:27:21 2023

@author: psakicki
"""

#### Import star style
from geodezyx import *                   # Import the GeodeZYX modules
from geodezyx.externlib import *         # Import the external modules
from geodezyx.megalib.megalib import *   # Import the legacy modules names

import autorino.convert.conv_batch as cvb

###################### OVSM for SONEL
psitelogs = "/work/sitelogs/SITELOGS"


#p="/net/baiededix/ovsm/ACQUI/Deformations/GPS/data" 
#regex=".*(ILAM|BIM0|SAM0|MFO0).*"
regex=".*"
keywords_path_excl=[]


########## complete repro 2017-2023 process 
flist = "/home/sakic/090_TEMP/Raw_all_MQ_mk01a.list"

outdir = "/scratch/convgnss/063_big_conv_MQ_2017"
nyear = 8
minyear = 2017
maxyear = 2017

outdir = "/scratch/convgnss/064_big_conv_MQ_2018"
nyear = 8
minyear = 2018
maxyear = 2018

outdir = "/scratch/convgnss/061_big_conv_MQ_2019_23"
nyear = 8
minyear = 2019
maxyear = 2023

outdir = "/scratch/convgnss/065_big_conv_MQ_2017_MLM0"
regex=".*MLM0.*"
nyear = 8
minyear = 2017
maxyear = 2017


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
