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
regex=".*"
keywords_path_excl=[]


########## process SONEL
flist = "/home/sakic/090_TEMP/Raw_sonel_GL_mk01a.list"
outdir = "/scratch/convgnss/021_SONEL_conv_GP"
nyear = 7
minyear = 2018
maxyear = 2023

########## process DOME
flist = "/home/sakic/090_TEMP/Raw_dome_GL_mk01a.list"
outdir = "/scratch/convgnss/051_dome_conv_GL"
nyear = 6
minyear = 2018
maxyear = 2023

########## process ALL
flist = "/home/sakic/090_TEMP/Raw_all_GL_mk01a.list"
outdir = "/scratch/convgnss/053_big_conv_GL_2016"
outdir = "/scratch/convgnss/054_big_conv_GL_2018"
regex=".*(ABD0|ABG0|ADE0|AGAL|AMC0|ASF0|BULG|CBE0|CRA2|DEHA|DHS0|DSD0|F562|F8O2|FFE0|FNA0|FNG0|HOUE|LDIS|LEN0|MAD0|MGL0|PAR1|PSA1|SBL0|SOUF|STG0|STMT|TAR1|TDB0).*"
nyear = 6
minyear = 2018
maxyear = 2018

########## process ALL 2011-2015
flist = "/home/sakic/090_TEMP/Raw_all_GL_mk01a.list"
outdir = "/scratch/convgnss/055_big_conv_GL_2011_15"
# HOUE et SOUF excluded
regex=".*(ABD0|ABG0|ADE0|AGAL|AMC0|ASF0|BULG|CBE0|CRA2|DEHA|DHS0|DSD0|F562|F8O2|FFE0|FNA0|FNG0|LDIS|LEN0|MAD0|MGL0|PAR1|PSA1|SBL0|STG0|STMT|TAR1|TDB0).*"
nyear = 6
minyear = 2011
maxyear = 2015

########## process IPGP coloc with TERIA ALL 2019-2023
flist = "/home/sakic/090_TEMP/Raw_all_GL_mk01a.list"
outdir = "/scratch/convgnss/057_big_conv_GL_IPcoTE_2019_2023-131"
regex=".*(ABD0|ASF0|CBE0|DEHA|FFE0|FNA0|HOUE|LDIS|STMT).*"
nyear = 6
minyear = 2019
maxyear = 2023

########## process mysteriously missing for 2022
#flist="/work/packets_manual/input_lists/GL_NoTeria_2022missing_run01/000_identification_lists/2022missing_RAW_OK_but_noSBL0_mk02b.list"
flist="/work/packets_manual/input_lists/GL_NoTeria_2022missing_run01/000_identification_lists/2022missing_RAW_STG0for2023_mk01a.list"  
outdir = "/scratch/convgnss/051_big_conv_GL_2022missing"
#keywords_path_excl=["TDB0"]
regex=".*"
nyear = 6
minyear = 2023
maxyear = 2023
########## process 2023 100-231 for FrBe  
flist = "/home/sakic/090_TEMP/Raw_GL_2023_100_231_forFB_mk01a.list" 
flist = "/home/sakic/090_TEMP/Raw_GL_2023_100_246_forFB_mk02a.list" 
outdir = "/scratch/convgnss/056_big_conv_GL_2023_100-231"
regex = ".*"
nyear = 6
minyear = 2023
maxyear = 2023

########## process old ashtech 2000-2016
flist = "/home/sakic/090_TEMP/Raw_all_GL_mk01a.list"
outdir = "/scratch/convgnss/058_big_conv_GL_old_ashtech"
# HOUE et SOUF excluded
#regex=".*(ABD0|ABG0|ADE0|AGAL|AMC0|ASF0|BULG|CBE0|CRA2|DEHA|DHS0|DSD0|F562|F8O2|FFE0|FNA0|FNG0|LDIS|LEN0|MAD0|MGL0|PAR1|PSA1|SBL0|STG0|STMT|TAR1|TDB0).*"
regex=".*(HOUE).*"
nyear = 6
minyear = 2000
maxyear = 2016



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
