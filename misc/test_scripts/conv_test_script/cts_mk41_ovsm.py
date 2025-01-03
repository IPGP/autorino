#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  7 16:29:30 2024

@author: psakicki
"""

import autorino
import autorino.api as aroapi

from geodezyx import utils

p = "/home/sakic/050_GNSS_input_data_baiededix/OVSM"
l = utils.find_recursive(p,"*202*BNX")

print(l)

out = "/home/sakic/031_SCRATCH_CONV/069_trm_MQ"
aroapi.convert_rnx(l,out,out)

