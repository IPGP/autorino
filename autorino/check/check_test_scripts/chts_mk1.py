#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 27 17:31:26 2023

@author: psakicki
"""

from autorino import check as arochk
import datetime as dt

p="/home/sakic/031_SCRATCH_CONV/062_big_conv_MQ_2017/rinexmoded"
p="/work/delivery/tags/GNSS_20230622080039_GL_NoTeria_2019-2023-099_run02B_aa/data"
start = dt.datetime(2017,4,1)
end = dt.datetime(2017,4,30)

arochk.check_rinex(p, start, end, return_concat_df=1)
