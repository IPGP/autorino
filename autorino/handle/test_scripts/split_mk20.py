#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 27/08/2024 10:41:29

@author: psakic
"""

import autorino.api as aroapi
import autorino.common as arocmn
from geodezyx import utils
import datetime as dt

p = "/home/psakicki/autorino_workflow_tests/conv_tests/CFNG00REU/2024"
L = utils.find_recursive(p, "*gz")

tmp_dir = "/home/psakicki/autorino_workflow_tests/tmp"
out_dir = "/home/psakicki/autorino_workflow_tests/split"

s = dt.datetime(2024, 2, 27, 1)
e = dt.datetime(2024, 2, 27, 3)
period = "5min"

epo = arocmn.EpochRange(s, e, period)

aroapi.split_rnx(
    L, s, e, period, tmp_dir, out_dir, tmp_dir, site="CFNG00REU", data_frequency="01S"
)
