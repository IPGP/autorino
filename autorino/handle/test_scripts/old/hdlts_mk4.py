#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 16 12:17:17 2024

@author: psakicki
"""

import autorino.common as arocmn
import autorino.handle as arohdl
from geodezyx import utils

tmp_dir = '/home/psakicki/autorino_workflow_tests/temp'
out_dir = '/home/psakicki/autorino_workflow_tests/handle'
log_dir = tmp_dir

epo = arocmn.epoch_range.create_dummy_epochrange()
hdl = arohdl.HandleGnss(out_dir, tmp_dir, log_dir, epo) #, site_id='CFNG')

p="/home/psakicki/autorino_workflow_tests/conv_tests/CFNG00REU/2024"
L = utils.find_recursive(p,"*gz")

hdl.load_tab_filelist(L)
hdl.updt_epotab_rnx(use_rnx_filename_only=True)

a = hdl.group_by_epochs()






hdl.decompress()

hdl.print_table()
hdl.splice()
