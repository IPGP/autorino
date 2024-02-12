#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 22:04:01 2024

@author: psakicki
"""

#### Import star style
from geodezyx import *                   # Import the GeodeZYX modules
from geodezyx.externlib import *         # Import the external modules
from geodezyx.megalib.megalib import *   # Import the legacy modules names

import autorino as aro

import autorino.general as aaaa


epoch1 = dt.datetime(2023,1,1,15,30)
epoch2 = dt.datetime(2023,1,6,7,45)
e = aaaa.EpochRange(epoch1, epoch2,'5min')


l = e.epoch_range_list()

s = pd.Series(l)

i = pd.Index(l)

s.dt.floor("24H")