#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 15:47:05 2022

@author: psakic
"""
import pandas as pd

import autorino.common as arocmn
import autorino.cfgfiles as arocfg

pmain = '/home/psakicki/CODES/IPGP/autorino/configfiles/main/autorino_main_cfg_exemple.yml'
psite = '/home/psakicki/CODES/IPGP/autorino/configfiles/sites/autorino_site_cfg_exemple.yml'

# CFNG

#out = arocfg.read_configfile_sessions_list(psite)
out = arocfg.read_cfg(psite, main_cfg_path=pmain)

a = arocmn.EpochRange(pd.NaT,pd.NaT)
a.eporng_list()