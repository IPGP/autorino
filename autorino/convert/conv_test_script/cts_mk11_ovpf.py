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



###################### OVPF
psitelogs = "/work/sitelogs/SITELOGS"

########## MAIN 
if 0:
    p="/net/baiededix/ovpf/miroir_ovpf/DonneesAcquisition/geodesie/GPSPermanent/" 
    regex=".*(FEUG|GBNG|GBSG|HDLG|TRCG).*"
    regex=".*(BOMG|BORG|C98G|CASG|CRAG|DERG|DSRG|ENCG|ENOG|FERG|FEUG|FJAG|FOAG|FREG|GB1G|GBNG|GBSG|GITG|GLOR|GPNG|GPSG|HDLG|KNKL|MABE|MAIG|MANB|MTSB|PBRG|PMZI|PRAG|PVDG|RVAG|RVLG|SAND|SNEG|TRCG).*"
    flist = utils.find_recursive(p,regex,case_sensitive=False)
elif 1:
    flist="/home/sakic/020_TEMP/Raw_PF_mk01a.list"
    flist="/home/sakic/020_TEMP/Raw_PF_mk02a.list"
    regex=".*"
else:
    print("toto")
nyear = 8
#minyear = 2018
#maxyear = 2018

#### OUT DIRECTORY
#outdir = "/scratch/convgnss/040_big_conv_PF/"
keywords_path_excl=['Problem','Rinex','ZIP',"MAIG","MABE","MANB","SAND"]


########## SANDBOX
# outdir = "/scratch/convgnss/049_big_conv_PF_sandbox/"
# minyear = 2022
# maxyear = 2022


########## 2022 process 
#flist = "/home/sakic/020_TEMP/Raw_PF_mk02a_2022.list"
#outdir = "/scratch/convgnss/042_big_conv_PF_2022"
#minyear = 2022
#maxyear = 2022


########## 2023 process 
flist="/home/sakic/020_TEMP/Raw_PF_mk04a.list"
##  regex=".*(BOMG|BORG|C98G|CASG|CRAG|DERG|DSRG|ENCG|ENOG|FERG|FEUG|FJAG|FOAG|FREG|GB1G|GBNG|GBSG|GITG|GLOR|GPNG|GPSG|HDLG|KNKL|MABE|MAIG|MANB|MTSB|PBRG|PMZI|PRAG|PVDG|RVAG|RVLG|SAND|SNEG|TRCG).*"
outdir = "/scratch/convgnss/042_big_conv_PF_2023"
minyear = 2023
maxyear = 2023


########## GLOR test process 
flist="/home/sakic/020_TEMP/Raw_PF_mk04a.list"
regex=".*(GLOR).*"
outdir = "/scratch/convgnss/043_PF_test_GLOR_2023"
minyear = 2023
maxyear = 2023

########## 2017 process 
flist="/home/sakic/020_TEMP/Raw_PF_mk04a.list"
##  regex=".*(BOMG|BORG|C98G|CASG|CRAG|DERG|DSRG|ENCG|ENOG|FERG|FEUG|FJAG|FOAG|FREG|GB1G|GBNG|GBSG|GITG|GLOR|GPNG|GPSG|HDLG|KNKL|MABE|MAIG|MANB|MTSB|PBRG|PMZI|PRAG|PVDG|RVAG|RVLG|SAND|SNEG|TRCG).*"
regex=".*"
outdir = "/scratch/convgnss/044_big_conv_PF_2018"
minyear = 2018
maxyear = 2018



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
