#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 15:00:40 2024

@author: psakic
"""

import numpy as np
import pandas as pd


import autorino.general as arogen
import autorino.workflow as arowkf
import autorino.epochrange as aroepo

import autorino.session as aroses


# Create a logger object.
import logging
logger = logging.getLogger(__name__)

class HandleGnss(arowkf.WorkflowGnss):
    def __init__(self,session,epoch_range,out_dir):
        super().__init__(session,epoch_range,out_dir)
        
epo = aroepo.create_dummy_epochrange()
ses = aroses.create_dummy_session()

H = HandleGnss(ses, epo, out_dir='/tmp/')

H.guess_local_files()   
wrkflw_grp_lis = H.group_epochs() 

W = wrkflw_grp_lis[0]
W.update_epoch_range_from_table()

for t in H.table.groupby('epoch_rnd'):
    print(t)

H.print_table()
