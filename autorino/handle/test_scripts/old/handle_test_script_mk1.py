#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 16 12:17:17 2024

@author: psakicki
"""

#### Import star style
from geodezyx import *                   # Import the GeodeZYX modules
from geodezyx.externlib import *         # Import the external modules
from geodezyx.megalib.megalib import *   # Import the legacy modules names

import numpy as np
import pandas as pd


import autorino.general as arogen
#import autorino.workflow as arowkf
#import autorino.epochrange as aroepo
#import autorino.session as aroses
import autorino.handle as arohdl


epo = arogen.create_dummy_epochrange()
ses = arogen.create_dummy_session()

H = arohdl.HandleGnss(ses, epo, out_dir='/tmp/')

H.guess_local_files()   
wrkflw_grp_lis = H.group_epochs() 

W = wrkflw_grp_lis[0]
W.update_epoch_range_from_table()

# for t in H.table.groupby('epoch_rnd'):
#     print(t)

_ = H.print_table()
