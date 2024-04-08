#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import autorino.common as arocmn
import autorino.handle as arohdl

import os

def split_rnx(rnxs_inp,epo_inp,tmp_dir,out_dir,
              handle_software='converto'):

    ### define other dirs
    rnxmod_dir = os.path.join(tmp_dir,'rinexmoded')
    log_dir = tmp_dir

    #### define spt_store: the Split object which will store all the input RINEXs
    spt_store = arohdl.SplitGnss(out_dir, tmp_dir, log_dir)
    spt_store.load_table_from_filelist(rnxs_inp)
    spt_store.update_epoch_table_from_rnx_fname(use_rnx_filename_only=True)

    #### define spt_split: the Split object which will perform the split operation
    spt_split = arohdl.SplitGnss(out_dir, tmp_dir, log_dir, epo_inp)
    spt_split.find_rnxs_for_split(spt_store)
    spt_split.decompress()
    spt_split.split(handle_software=handle_software)

