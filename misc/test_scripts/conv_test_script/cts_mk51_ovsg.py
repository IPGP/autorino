#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  7 16:29:30 2024

@author: psakicki

Test the official Trimble converter
"""

import autorino.common as arocmn

path_list = "/scratch/temp_stuffs/GL_raw_2024_01b.list"
psitelogs = "/scratch/xchg_cdd/sitelogs/SITELOGS"

out = "/home/sakic/031_SCRATCH_CONV/021_GL_2024"
arocmn.convert_rnx(path_list,out,out,metadata=psitelogs)

