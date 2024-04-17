#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import autorino.common as arocmn
import autorino.handle as arohdl

import os

def splice_rnx(rnxs_inp,
               tmp_dir,out_dir,log_dir=None,
               handle_software='converto',
               period='1d',
               rolling_period=False,
               rolling_ref=-1,
               round_method='floor',
               drop_epoch_rnd=False,
               rinexmod_options=dict()):

    ### define other dirs
    if not log_dir:
        log_dir = tmp_dir

    #### define spc_inp: the Splice object which will store all the input RINEXs
    spc_inp = arohdl.SpliceGnss(out_dir, tmp_dir, log_dir)
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