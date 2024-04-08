#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 15:00:40 2024

@author: psakic
"""
import numpy as np

import autorino.common as arocmn
import autorino.convert as arocnv
import autorino.handle as arohdl

import datetime as dt

from geodezyx import utils


tmp_dir = '/home/psakicki/autorino_workflow_tests/temp'
out_dir = '/home/psakicki/autorino_workflow_tests/handle'

epo = arocmn.EpochRange(dt.datetime(2024, 2, 28, 1),
                        dt.datetime(2024, 2, 28, 3),
                        '5min')

p = "/home/psakicki/autorino_workflow_tests/conv_tests/CFNG00REU/2024"
L = utils.find_recursive(p, "*gz")

arohdl.split_rnx(epo,L,tmp_dir,out_dir)