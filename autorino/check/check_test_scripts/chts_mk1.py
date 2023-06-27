#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 27 17:31:26 2023

@author: psakicki
"""

from autorino import check as arch
import datetime as dt

p="/home/sakic/031_SCRATCH_CONV/062_big_conv_MQ_2017/rinexmoded"
start = dt.datetime(2017,4,1)
end = dt.datetime(2017,4,30)

arch.check_rinex(p, start, end, return_concat_df=1)
