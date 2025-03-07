#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  7 14:27:21 2023

@author: psakicki
"""

import yaml

import autorino.convert as arcv
from autorino import configread as arcfg
#### Import star style
from geodezyx import *  # Import the GeodeZYX modules
from geodezyx.externlib import *  # Import the external modules

pconfig = "/home/gps/tests_pierres/autorino/configfiles/proto_config_HOUE_03a.yml"
pconfig = "/home/gps/tests_pierres/autorino/configfiles/proto_config_PSA1_03a.yml"

pconfig = "/home/sakic/010_CODES/autorino/configfiles/proto_config_HOUE_03a.yml"

Y1 = yaml.safe_load(open(pconfig))

SESlist, REQlist = arcfg.session_request_from_configfile(pconfig)
#REQ = REQlist[1]
SES = SESlist
REQ = REQlist
EPOC = REQ.epoch_range

pout = "/home/sakic/020_TEMP/convcls_test"
psitelogs = "/work/metadata/SITELOGS"

CONV = arcv.ConvertGnss(SES,
                        EPOC,
                        pout,
                        pout,
                        psitelogs)


flist = "/home/sakic/020_TEMP/Raw_all_MQ_mk01a.list"
flist = "/home/sakic/020_TEMP/Raw_dome_GL_mk01a.list"

### find and read previous table log files


prev_table_logs = utils.find_recursive(pout,'*table.log')    
if prev_table_logs:
    DF_prev_tbl = pd.concat([pd.read_csv(f) for f in prev_table_logs])
    DF_prev_tbl.reset_index(inplace=True,drop=True)

    #print(DF_prev_tbl)


CONV.load_tab_filelist(flist)
#CONV.filter_bad_keywords(['Problem','Rinex','ZIP'])
CONV.filter_year_min_max(2019,2020)

# if prev_table_logs:
#     CONV.filter_prev_tab(DF_prev_tbl)

CONV.conv_rnxmod_files()

