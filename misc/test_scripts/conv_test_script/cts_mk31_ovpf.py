#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  7 14:27:21 2023

@author: psakicki
"""

import autorino.convert as arcv
#### Import star style
from geodezyx import *  # Import the GeodeZYX modules
from geodezyx.externlib import *  # Import the external modules

#from autorino import epochrange as aroepo
#from autorino import  session as aroses

##### 2023
flist="/scratch/temp_stuffs/Raw_PF_2023_365_topcon_mk1a.list"
flist="/home/sakic/090_TEMP/Raw_PF_2023_100_265_mk01a.list"
flist="/home/sakic/090_TEMP/Raw_PF_TKRG_CFNG_2023_mk1.list"
regex=".*"
pout = "/scratch/convgnss/044_PF_CFNG_TKRG_2023"
minyear = 2023
maxyear = 2024
nyear = 5


psitelogs = "/work/metadata/SITELOGS"

CONV = arcv.ConvertGnss(pout, pout, pout,
                        metadata=psitelogs)




### find and read previous table log files


prev_table_logs = utils.find_recursive(pout,'*table.log')    
if prev_table_logs and False:
    DF_prev_tbl = pd.concat([pd.read_csv(f) for f in prev_table_logs])
    DF_prev_tbl.reset_index(inplace=True,drop=True)

    #print(DF_prev_tbl)


CONV.load_table_from_filelist(flist)
CONV.print_table()
#CONV.filter_bad_keywords(['Problem','Rinex','ZIP'])
#CONV.filter_year_min_max(2019,2020)

# if prev_table_logs:
#     CONV.filter_previous_tables(DF_prev_tbl)

CONV.convert(force=True)




