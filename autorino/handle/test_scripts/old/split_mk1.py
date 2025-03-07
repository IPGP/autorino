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

tmp_dir = "/home/psakicki/autorino_workflow_tests/temp"
rnxmod_dir = "/home/psakicki/autorino_workflow_tests/rinexmoded"

out_dir = "/home/psakicki/autorino_workflow_tests/handle"
log_dir = tmp_dir

epo_dummy = arocmn.epoch_range.create_dummy_epochrange()
hdl_store = arohdl.HandleGnss(out_dir, tmp_dir, log_dir, epo_dummy)  # , site_id='CFNG')

p = "/home/psakicki/autorino_workflow_tests/conv_tests/CFNG00REU/2024"
L = utils.find_recursive(p, "*gz")

hdl_store.load_tab_filelist(L)
hdl_store.updt_epotab_rnx(use_rnx_filename_only=True)

epo = arocmn.EpochRange(
    dt.datetime(2024, 2, 28, 1), dt.datetime(2024, 2, 28, 3), "5min"
)

hdl_split = arohdl.HandleGnss(out_dir, tmp_dir, log_dir, epo)

hdl_split.feed_by_epochs(hdl_store)

handle_software = "converto"

hdl_split.decompress()

# hdl_split.split()

# def split(self):
for irow, row in hdl_split.table.iterrows():

    rinexmod_kwargs = {  #'marker': 'TOTO',
        "compression": "gz",
        "longname": True,
        #'sitelog': metadata,
        "force_rnx_load": True,
        "verbose": False,
        "tolerant_file_period": True,
        "full_history": True,
    }

    hdl_split.on_row_split(irow, tmp_dir)

    hdl_split.mono_rinexmod(irow, rnxmod_dir, rinexmod_kwargs)

    hdl_split.mono_mv_final(irow)
