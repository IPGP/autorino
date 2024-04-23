#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 23/04/2024 14:21:56

@author: psakic
"""

import autorino.convert as arocnv
import autorino.handle as arohdl

def convert_rnx(rnxs_inp, tmp_dir, out_dir, log_dir=None,
                rinexmod_options=None,
                metadata=None):
    ### define other dirs
    if not log_dir:
        log_dir = tmp_dir

    #### define spt_store: the Split object which will store all the input RINEXs
    cnv = arocnv.ConvertGnss(out_dir, tmp_dir, log_dir,
                             metadata=metadata)

    cnv.load_table_from_filelist(rnxs_inp)
    # cnv.update_epoch_table_from_rnx_fname(use_rnx_filename_only=True)

    cnv.convert(force=True,  ### always force (so far), because we can't guess local RINEX
                rinexmod_options=rinexmod_options)

    return None


def split_rnx(rnxs_inp, epo_inp, tmp_dir, out_dir, log_dir = None,
              handle_software='converto',
              rinexmod_options=None,
              metadata=None):
    ### define other dirs
    if not log_dir:
        log_dir = tmp_dir

    #### define spt_store: the Split object which will store all the input RINEXs
    spt_store = arohdl.HandleGnss(out_dir, tmp_dir, log_dir,
                                  metadata=metadata)
    spt_store.load_table_from_filelist(rnxs_inp)
    spt_store.update_epoch_table_from_rnx_fname(use_rnx_filename_only=True)

    #### define spt_split: the Split object which will perform the split operation
    spt_split = arohdl.HandleGnss(out_dir, tmp_dir, log_dir, epo_inp,
                                  metadata=metadata)
    spt_split.find_rnxs_for_handle(spt_store)

    spt_split.split(handle_software=handle_software,
                    rinexmod_options=rinexmod_options)
    return None


def splice_rnx(rnxs_inp,
               tmp_dir, out_dir, log_dir=None,
               handle_software='converto',
               period='1d',
               rolling_period=False,
               rolling_ref=-1,
               round_method='floor',
               drop_epoch_rnd=False,
               rinexmod_options=None,
               metadata=None):
    ### define other dirs
    if not log_dir:
        log_dir = tmp_dir

    #### define spc_inp: the Splice object which will store all the input RINEXs
    spc_inp = arohdl.HandleGnss(out_dir, tmp_dir, log_dir,
                                metadata=metadata)
    spc_inp.load_table_from_filelist(rnxs_inp)
    spc_inp.update_epoch_table_from_rnx_fname(use_rnx_filename_only=True)

    ### divide_by_epochs will create several SpliceGnss objects
    spc_main_obj, spc_objs_lis = spc_inp.divide_by_epochs(period=period,
                                                          rolling_period=rolling_period,
                                                          rolling_ref=rolling_ref,
                                                          round_method=round_method,
                                                          drop_epoch_rnd=drop_epoch_rnd)

    spc_main_obj.splice(handle_software=handle_software,
                        rinexmod_options=rinexmod_options)

    return spc_main_obj
