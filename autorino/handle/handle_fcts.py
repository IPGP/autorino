#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import autorino.common as arocmn
import autorino.handle as arohdl

from geodezyx import utils
import datetime as dt
import os

def split_frontend(epo_in,rnxs_inp,tmp_dir,out_dir,
                   handle_software='converto'):

    ### define other dirs
    rnxmod_dir = os.path.join(tmp_dir,'rinexmoded')
    log_dir = tmp_dir

    #### define hdl_store: the Handle object which will store the input RINEXs
    epo_dummy = arocmn.epoch_range.create_dummy_epochrange()
    hdl_store = arohdl.HandleGnss(out_dir, tmp_dir, log_dir, epo_dummy)  # , site_id='CFNG')
    hdl_store.load_table_from_filelist(rnxs_inp)
    hdl_store.update_epoch_table_from_rnx_fname(use_rnx_filename_only=True)

    #### define hdl_split: the Handle object which will perform the split operation
    hdl_split = arohdl.HandleGnss(out_dir, tmp_dir, log_dir, epo)
    hdl_split.find_rnxs_for_split(hdl_store)
    hdl_split.decompress_table()
    hdl_split.split_table()


tmp_dir = '/home/psakicki/autorino_workflow_tests/temp'
out_dir = '/home/psakicki/autorino_workflow_tests/handle'

epo = arocmn.EpochRange(dt.datetime(2024, 2, 28, 1),
                        dt.datetime(2024, 2, 28, 3),
                        '5min')

p = "/home/psakicki/autorino_workflow_tests/conv_tests/CFNG00REU/2024"
L = utils.find_recursive(p, "*gz")

split_frontend(epo,L,tmp_dir,out_dir)