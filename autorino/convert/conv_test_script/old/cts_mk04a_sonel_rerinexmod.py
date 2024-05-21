#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  4 14:48:49 2023

@author: psakicki
"""

#### Import star style


import rinexmod_api

# flist = utils.find_recursive(p,regex,
#                              case_sensitive=False)


########### SITELOGS
psitelogs = "/work/metadata/SITELOGS"
sitelogs = rinexmod_api.sitelog_input_manage(psitelogs,force=False)


# print("TOTOTOTO")
# print(os.path.isfile("/scratch/convgnss/020_SONEL_conv/converted/GBSG201801130000A.18o"))

# rinexmod_api.RinexFile("/scratch/convgnss/020_SONEL_conv/converted/GBSG201801130000A.18o")


p = "/scratch/convgnss/021_SONEL_conv_GP/logs/20230331_121342_rnx_fail.log"
p = "/scratch/convgnss/020_SONEL_conv/logs/20230329_183028_rnx_fail.log"
flist = open(p).readlines()

outdir_rinexmoded_use = '/scratch/convgnss/022_SONEL_conv_redo'

for frnxtmp in flist:
    try:
        rinexmod_api.rinexmod(frnxtmp,
                              outdir_rinexmoded_use,
                              compression=None,
                              longname=True,
                              sitelog=sitelogs,
                              force_rnx_load=True,
                              verbose=True,
                              full_history=True)
    except:
        continue