#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 15:47:05 2022

@author: psakic
"""


import autorino.config as arocfg
import autorino.common as arocmn
import pandas as pd


pmain = '/home/psakicki/CODES/IPGP/autorino/configfiles/autorino_main_cfg_01a.yml'
psite = '/home/psakicki/CODES/IPGP/autorino/configfiles/autorino_site_cfg_08a_CFNG.yml'

#out = arocfg.read_configfile_sessions_list(psite)
out = arocfg.read_cfg(psite, main_cfg_path=pmain)

out

a = arocmn.EpochRange(pd.NaT,pd.NaT)
a.epoch_range_list()