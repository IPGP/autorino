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

import autorino.convert as arocnv
import autorino.common  as arocmn

import yaml

import timeit

##### 2023
flist="/scratch/temp_stuffs/Raw_PF_2023_365_topcon_mk1a.list"
flist="/home/sakic/090_TEMP/Raw_PF_2023_100_265_mk01a.list"
flist="/home/sakic/090_TEMP/Raw_PF_TKRG_CFNG_2023_mk1.list"
regex=".*"
p = "/scratch/convgnss/044_PF_CFNG_TKRG_2023/"
plog = p + '/log' 
ptmp = p + '/tmp' 
pout = p + '/out' 
minyear = 2023
maxyear = 2024
nyear = 5


psitelogs = "/work/sitelogs/SITELOGS"

CONV = arocnv.ConvertGnss(pout,ptmp,plog,
                          sitelogs=psitelogs)




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




