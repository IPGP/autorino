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

import rinexfile


#p = "/home/sakic/031_SCRATCH_CONV/058_big_conv_GL_old_ashtech/rinexmoded/HOUE"
#p = "/home/sakic/031_SCRATCH_CONV/058_big_conv_GL_old_ashtech/rinexmoded2/HOUE"
p = "/home/sakic/031_SCRATCH_CONV/075_HOUE_week_corr_ON/"  
p = "/home/sakic/030_SCRATCH/convgnss/058_big_conv_GL_old_ashtech/"
p = "/home/sakic/030_SCRATCH/convgnss/065_big_conv_MQ_2017_MLM0/"

p = "/home/sakic/031_SCRATCH_CONV/046_big_conv_PF_GB1G_2017_18/"
pinp = p + "/gfzrnxed"  
pout = p + "/gfzrnxed_clean"  


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

    R = rinexfile.RinexFile(rnxs_str)
    R.clean_gfzrnx_comments(True,False)

    sysobs,_ = R.get_sys_obs_types()

    systems = sysobs.keys()

    

    sysobsG = sysobs["G"]
    sysobsGout  = []
    for e in  sysobsG:
        if len(e) == 2:
            if e[1] == "2":
                sysobsGout.append(e + "W")
            elif e[1] == "1":
                sysobsGout.append(e + "C")
            else:
                sysobsGout.append(e)
        else:
            sysobsGout.append(e)



    
    print(sysobsG) 
    print(sysobsGout) 


    dicsysout = dict()
    dicsysout["G"] = sysobsGout 

    R.mod_sys_obs_types({"G" : sysobsGout })

    R.get_longname(inplace_set=True)
    print("Final Filename",R.filename)

    R.write_to_path(pout_site)

 
 ##### then RINEXMOD command
 # rinexmod --sitelog /work/sitelogs/SITELOGS -t -c 'gz' -r '/home/sakic/031_SCRATCH_CONV/075_HOUE_week_corr_ON/gfzrnxed_clean' -m "HOUZ"  ./old_houe_01a.list ./rerinexmoded

