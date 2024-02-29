#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 29 17:25:11 2024

@author: psakic
"""

import autorino.common as arocmn
import autorino.handle as arohdl
import autorino.convert as arocnv

from geodezyx import utils
import datetime as dt
import pandas as pd
import numpy as np

tmp_dir = '/home/psakicki/autorino_workflow_tests/temp'
out_dir = '/home/psakicki/autorino_workflow_tests/handle'
log_dir = tmp_dir

epo_dummy = arocmn.epoch_range.create_dummy_epochrange()
hdl_store = arohdl.HandleGnss(out_dir, tmp_dir, log_dir, epo_dummy) #, site_id='CFNG')

p="/home/psakicki/autorino_workflow_tests/conv_tests/CFNG00REU/2024"
L = utils.find_recursive(p,"*gz")

hdl_store.load_table_from_filelist(L)
hdl_store.update_epoch_table_from_rnx_fname(use_rnx_filename_only=True)

epo = arocmn.EpochRange(dt.datetime(2024,2,28,1),
                        dt.datetime(2024,2,28,3),
                        '5min')

hdl_split = arohdl.HandleGnss(out_dir, tmp_dir, log_dir, epo)

hdl_split.find_rnxs_for_split(hdl_store)

handle_software = 'converto'

hdl_split.decompress_table()

hdl_split.split()

#def split(self):
for irow,row in hdl_split.table.iterrows():

    frnx_inp = row['fpath_inp']

    tmp_dir_use = hdl_split.translate_path(self.tmp_dir)
    out_dir_use = hdl_split.translate_path(self.out_dir)

    if handle_software == 'converto':
        converto_kwoptions={'-st':row['epoch_srt'].strftime('%Y%m%d%H%M%S'),
                            '-e': row['epoch_end'].strftime('%Y%m%d%H%M%S')}

        frnxtmp, _ = arocnv.converter_run(frnx_inp,
                                          tmp_dir_use,
                                          'converto',
                                          bin_kwoptions=converto_kwoptions)
    elif handle_software == 'gfzrnx':
        gfzrnx_kwoptions = {'-epo_beg': row['epoch_srt'].strftime('%Y%m%d_%H%M%S'),
                            '-d': int((row['epoch_end'] - row['epoch_srt']).total_seconds())}

        frnxtmp, _ = arocnv.converter_run(frnx_inp,
                                          tmp_dir_use,
                                          'gfzrnx',
                                          bin_kwoptions=gfzrnx_kwoptions)








