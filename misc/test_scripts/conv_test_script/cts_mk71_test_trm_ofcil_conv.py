#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  7 16:29:30 2024

@author: psakicki

Test the official Trimble converter
"""

import autorino.api as aroapi
from geodezyx import utils

p = "/home/sakic/050_GNSS_input_data_baiededix/OVSG_raw"
l = utils.find_recursive(p,"*PSA1*T02")


psitelogs = "/scratch/xchg_cdd/sitelogs/SITELOGS"


print(l)

out = "/home/sakic/031_SCRATCH_CONV/071_test_trm_oficl_conv"
aroapi.convert_rnx(l,out,out,metadata=psitelogs)

