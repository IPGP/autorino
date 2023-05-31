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

###################### OVSG for SONEL
psitelogs = "/work/sitelogs/SITELOGS"


#p="/net/baiededix/ovsm/ACQUI/Deformations/GPS/data" 
#regex=".*(ILAM|BIM0|SAM0|MFO0).*"
regex=".*(TDB0|MGL0|DHS0|ADE0|DSD0|DHS0).*"
regex=".*"
keywords_path_excl=[]

########## process SONEL
flist = "/home/sakic/020_TEMP/Raw_sonel_GL_mk01a.list"
outdir = "/scratch/convgnss/021_SONEL_conv_GP"
nyear = 7
minyear = 2018
maxyear = 2023

########## process DOME
flist = "/home/sakic/020_TEMP/Raw_dome_GL_mk01a.list"
outdir = "/scratch/convgnss/051_dome_conv_GL"
nyear = 6
minyear = 2018
maxyear = 2023

########## process ALL
flist = "/home/sakic/020_TEMP/Raw_all_GL_mk01a.list"
outdir = "/scratch/convgnss/051_big_conv_GL_2022a"
regex=".*(ABD0|ABG0|ADE0|AGAL|AMC0|ASF0|BULG|CBE0|CRA2|DEHA|DHS0|DSD0|F562|F8O2|FFE0|FNA0|FNG0|HOUE|LDIS|LEN0|MAD0|MGL0|PAR1|PSA1|SBL0|SOUF|STG0|STMT|TAR1|TDB0).*"
nyear = 6
minyear = 2022
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
