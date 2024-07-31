#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 15:00:40 2024

@author: psakic
"""

import datetime as dt

import autorino.common as arocmn
from geodezyx import utils

tmp_dir = '/home/psakicki/autorino_workflow_tests/tmp'
out_dir = '/home/psakicki/autorino_workflow_tests/split'

epo = arocmn.EpochRange(dt.datetime(2024, 2, 28, 1),
                        dt.datetime(2024, 2, 28, 3),
                        '5min')

epo = (dt.datetime(2024, 2, 28, 1),
       dt.datetime(2024, 2, 28, 3),
       '5min')

p = "/home/psakicki/autorino_workflow_tests/conv_tests/CFNG00REU/2024"
L = utils.find_recursive(p, "*gz")

arocmn.split_rnx(L,epo,tmp_dir,out_dir,tmp_dir)