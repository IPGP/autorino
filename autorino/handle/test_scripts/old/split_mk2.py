#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 29 17:25:11 2024

@author: psakic
"""

import datetime as dt

import autorino.common as arocmn
import autorino.handle as arohdl
from geodezyx import utils

tmp_dir = '/home/ovsgnss/090_TEMP_STUFFS/autorino_workflow_tests/temp'
rnxmod_dir = '/home/ovsgnss/090_TEMP_STUFFS/autorino_workflow_tests/rinexmoded'

out_dir = '/home/ovsgnss/090_TEMP_STUFFS/autorino_workflow_tests/handle'
log_dir = tmp_dir

p="/home/ovsgnss/090_TEMP_STUFFS/2402_tests_PF_pride"
L = utils.find_recursive(p,"*BORG*crx*gz")


epo_dummy = arocmn.epoch_range.create_dummy_epochrange()
hdl_store = arocmn.StepGnss(out_dir, tmp_dir, log_dir, epoch_range=None) #, site_id='CFNG')
hdl_store.load_table_from_filelist(L)
hdl_store.updt_epotab_rnx(use_rnx_filename_only=True)

epo = arocmn.EpochRange(dt.datetime(2023,6,4),
                        dt.datetime(2023,7,31),
                       # dt.datetime(2023,6,4,0,30),
                        '15min')

splt = arohdl.HandleGnss(out_dir, tmp_dir, log_dir, epo)
splt.feed_by_epochs(hdl_store)

handle_software = 'gfzrnx'

splt.decompress()
splt.split(handle_software='gfzrnx')









