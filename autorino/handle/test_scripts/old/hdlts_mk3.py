#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 16 12:17:17 2024

@author: psakicki
"""

import autorino.general as arogen

import autorino.handle as arohdl

tmp_dir = "/home/psakicki/autorino_workflow_tests/temp"
out_dir = "/home/psakicki/autorino_workflow_tests/handle"
log_dir = tmp_dir

epo = arogen.epoch_range.create_dummy_epochrange()
hdl = arohdl.HandleGnss(out_dir, tmp_dir, log_dir, epo, site_id="CFNG")

from geodezyx import utils

p = "/home/psakicki/autorino_workflow_tests/conv_tests/CFNG00REU/2024/024"
L = utils.find_recursive(p, "*gz")

hdl.load_tab_filelist(L)
hdl.updt_epotab_rnx()

# bool_comp = hdl.table['fpath_inp'].apply(arocmn.is_compressed)
# idx_comp = hdl.table.loc[bool_comp].index
# hdl.table.loc[idx_comp,'fpath_ori'] = hdl.table[idx_comp,'fpath_inp']
# files_out = self.table.loc[idx_comp,table_col].apply(arocmn.decompress_file)
# self.table.loc[idx_comp,table_col] = files_out

hdl.decompress()

hdl.print_table()
hdl.splice()
