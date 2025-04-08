#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  2 14:35:28 2023

@author: psakic
"""

import rinexfile

#### Import star style
from geodezyx import *  # Import the GeodeZYX modules

# inpdir = "/home/sakic/031_SCRATCH_CONV/058_big_conv_GL_old_ashtech/rinexmoded/HOUE"
# inpdir = "/home/sakic/031_SCRATCH_CONV/058_big_conv_GL_old_ashtech/rinexmoded2/HOUE"
p = "/home/sakic/031_SCRATCH_CONV/075_HOUE_week_corr_ON/"
p = "/home/sakic/030_SCRATCH/convgnss/058_big_conv_GL_old_ashtech/"
p = "/home/sakic/030_SCRATCH/convgnss/065_big_conv_MQ_2017_MLM0/"

p = "/home/sakic/031_SCRATCH_CONV/046_big_conv_PF_GB1G_2017_18/"
pinp = p + "/gfzrnxed"
pout = p + "/gfzrnxed_clean"

p = "/work/work/TERIA_DATA/"
pinp = p + "/012_from_RGP_rnx3conv"
pout = p + "/013_from_RGP_rnx3conv_clean"

p = "/home/sakic/090_TEMP/GL_miss2to3/"
pinp = p + "/020_rnx3conv"
pout = p + "/030_rnx3conv_clean"


utils.create_dir(pout)

L = operational.rinex_finder(pinp, compressed=False)
DF = operational.read_rinex_list_table(L)

DF["day"] = DF.date.dt.floor("D")

print(DF)

DFgrp = DF.groupby(["site", "day"])

sysobs3char = dict()
sysobs3char["G"] = ["C", "W"]
sysobs3char["R"] = ["C", "P"]


for (site, day), df in DFgrp:
    print(df.name)
    rnxs_str = " ".join(df.path)
    pout_site = pout + "/" + site[:4]
    utils.create_dir(pout_site)

    R = rinexfile.RinexFile(rnxs_str)
    R.clean_gfzrnx_comments(True, False)

    sysobs, _ = R.get_sys_obs_types()

    systems = sysobs.keys()
    dicsysout = dict()

    for sys in systems:
        sysobsinp = sysobs[sys]
        sysobsout = []
        for e in sysobsinp:
            if len(e) == 2:
                if e[1] in ("1", "2"):
                    sysobsout.append(e + sysobs3char[sys][int(e[1]) - 1])
                else:
                    sysobsout.append(e)
            else:
                sysobsout.append(e)

        print("obs inp", sys, sysobsinp)
        print("obs out", sys, sysobsout)

        dicsysout[sys] = sysobsout

    R.mod_sys_obs_types(dicsysout)

    R.get_longname(inplace_set=True)
    print("Final Filename", R.filename)

    R.write_to_path(pout_site)


##### then RINEXMOD command
# rinexmod --sitelog /work/metadata/SITELOGS -t -c 'gz' -r '/home/sakic/031_SCRATCH_CONV/075_HOUE_week_corr_ON/gfzrnxed_clean' -m "HOUZ"  ./old_houe_01a.list ./rerinexmoded
