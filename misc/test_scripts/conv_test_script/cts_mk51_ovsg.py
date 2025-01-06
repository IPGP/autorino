#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  7 16:29:30 2024

@author: psakicki

"""

import autorino.api as aroapi

path_list = "/scratch/temp_stuffs/GL_raw_2024_01b_NO_Trimble_01a.list"
path_list = "/scratch/temp_stuffs/GL_raw_2024_01b_use.list"
psitelogs = "/scratch/xchg_cdd/sitelogs/SITELOGS"

out = "/home/sakic/031_SCRATCH_CONV/023_GL_2024"
aroapi.convert_rnx(path_list,out_dir=out,metadata=psitelogs)

