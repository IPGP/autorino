#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  7 14:27:21 2023

@author: psakicki
"""

import autorino.api as aroapi

flist="/scratch/temp_stuffs/Raw_PF_2024_001_207_mk01e.list"  
psitelogs = "/work/metadata/SITELOGS"
psitelogs = "/scratch/xchg_cdd/sitelogs/SITELOGS"
outdir="/home/sakic/031_SCRATCH_CONV/011_PF_2024_001_200"


aroapi.convert_rnx(flist,
                   outdir,
                   metadata=psitelogs)


