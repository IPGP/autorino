#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  2 14:35:28 2023

@author: psakic
"""

import hatanaka

#### Import star style
from geodezyx import *  # Import the GeodeZYX modules
from geodezyx.externlib import *  # Import the external modules

#inpdir = "/home/sakic/031_SCRATCH_CONV/058_big_conv_GL_old_ashtech/rinexmoded/HOUE"
#inpdir = "/home/sakic/031_SCRATCH_CONV/058_big_conv_GL_old_ashtech/rinexmoded2/HOUE"
p = "/home/sakic/031_SCRATCH_CONV/075_HOUE_week_corr_ON/"  
p = "/home/sakic/030_SCRATCH/convgnss/058_big_conv_GL_old_ashtech/"

p = "/home/sakic/031_SCRATCH_CONV/046_big_conv_PF_GB1G_2017_18/"

pinp = p + "/rinexmoded_all_ashtech_2011_2016"
pinp = p + "/rinexmoded"
pout = p + "/gfzrnxed"  


pinp = "/work/work/TERIA_DATA/010_from_RGP"
pout = "/work/work/TERIA_DATA/012_from_RGP_rnx3conv"

pinp = "/home/sakic/090_TEMP/GL_miss2to3/010_rnx2"
pout = "/home/sakic/090_TEMP/GL_miss2to3/020_rnx3conv"

utils.create_dir(pout)

one_day_compressed = True
day_filter = True
L = operational.rinex_finder(pinp,compressed=None)
DF = operational.read_rinex_list_table(L)

DF["day"] = DF.date.dt.floor("D") 


if day_filter:
    DF = DF[DF.day < dt.datetime(2020,9,26)]



print(DF)


DFgrp = DF.groupby(["site","day"])


for (site,day),df in DFgrp:
    print(df.name)
    if len(df) > 1 and one_day_compressed :
        continue
    rnxout_stk = []

    for rnx in df.path:
        rnxout = hatanaka.decompress_on_disk(rnx,skip_strange_epochs=True)
        rnxout_stk.append(str(rnxout))

    rnxs_str = " ".join(rnxout_stk)
    pout_site = pout + "/" + site[:4]

    utils.create_dir(pout_site)
    cmd_gfzrnx = "gfzrnx -finp " + rnxs_str + " -fout " + pout_site + "/::RX3::" 

    print(cmd_gfzrnx)

    process_converter = subprocess.run(cmd_gfzrnx,
                                       executable="/bin/bash",
                                       shell=True,
#                                       stdout=PIPE,
#                                       stderr=PIPE,
                                       timeout=60)
 

