#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  2 14:35:28 2023

@author: psakic
"""

#### Import star style
from geodezyx import *                   # Import the GeodeZYX modules
from geodezyx.externlib import *         # Import the external modules
from geodezyx.megalib.megalib import *   # Import the legacy modules names


#p = "/home/sakic/031_SCRATCH_CONV/058_big_conv_GL_old_ashtech/rinexmoded/HOUE"
#p = "/home/sakic/031_SCRATCH_CONV/058_big_conv_GL_old_ashtech/rinexmoded2/HOUE"
p = "/home/sakic/031_SCRATCH_CONV/075_HOUE_week_corr_ON/"  
p = "/home/sakic/030_SCRATCH/convgnss/058_big_conv_GL_old_ashtech/"
pinp = p + "/rinexmoded"
pinp = p + "/rinexmoded_all_ashtech_2011_2016"
pout = p + "/gfzrnxed"  


utils.create_dir(pout)


L = operational.rinex_finder(pinp,compressed=False)
DF = operational.read_rinex_list_table(L)

DF["day"] = DF.date.dt.floor("D") 


print(DF)


DFgrp = DF.groupby(["site","day"])


for (site,day),df in DFgrp:
    print(df.name)
    rnxs_str = " ".join(df.path)
    pout_site = pout + "/" + site[:4]
    utils.create_dir(pout_site)
    cmd_gfzrnx = "gfzrnx -finp " + rnxs_str + " -fout  " + pout_site + "/::RX3::" 

    process_converter = subprocess.run(cmd_gfzrnx,
                                       executable="/bin/bash",
                                       shell=True,
#                                       stdout=PIPE,
#                                       stderr=PIPE,
                                       timeout=60)
 

