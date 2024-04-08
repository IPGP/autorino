#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 15:00:40 2024

@author: psakic
"""
import numpy as np

import autorino.common as arocmn
import autorino.convert as arocnv

import pandas as pd
import os

# Create a logger object.
import logging

logger = logging.getLogger(__name__)


#   _____       _ _
#  / ____|     | (_)
# | (___  _ __ | |_  ___ ___
#  \___ \| '_ \| | |/ __/ _ \
#  ____) | |_) | | | (_|  __/
# |_____/| .__/|_|_|\___\___|
#        | |
#        |_|

class SpliceGnss(arocmn.StepGnss):
    def __init__(self, out_dir, tmp_dir, log_dir,
                 epoch_range=None,
                 site=None,
                 session=None,
                 options=None):

        super().__init__(out_dir, tmp_dir, log_dir,
                         epoch_range=epoch_range,
                         site=site,
                         session=session,
                         options=options)

    def divide_by_epochs(self,
                         period='1d',
                         rolling_period=False,
                         rolling_ref=-1,
                         round_method='floor',
                         drop_epoch_rnd=False):

        epoch_rnd = arocmn.round_epochs(self.table['epoch_srt'],
                                        period=period,
                                        rolling_period=rolling_period,
                                        rolling_ref=rolling_ref,
                                        round_method=round_method)

        self.table['epoch_rnd'] = epoch_rnd


        # get the main Handle object which will describe the final spliced RINEXs
        spc_main_obj_epoch_range = arocmn.EpochRange(np.min(epoch_rnd),
                                                     np.max(epoch_rnd),
                                                     period=period,
                                                     round_method=round_method)

        spc_main_obj = SpliceGnss(out_dir=self.out_dir,
                                  tmp_dir=self.tmp_dir,
                                  log_dir=self.log_dir,
                                  epoch_range=spc_main_obj_epoch_range,
                                  site=self.site,
                                  session=self.session)

        # get individual Handle objects
        grps = self.table.groupby('epoch_rnd')

        spc_obj_lis_out = []

        for i_tabgrp, (t_tabgrp, tabgrp) in enumerate(grps):
            spc_obj = self.copy()

            if drop_epoch_rnd:
                tabgrp_bis = tabgrp.drop('epoch_rnd', axis=1)
            else:
                tabgrp_bis = pd.DataFrame(tabgrp)

            spc_obj.table = tabgrp_bis
            spc_obj.update_epoch_range_from_table()
            spc_obj_lis_out.append(spc_obj)

            # fill the main object with the individuals
            # then "fpath_inp" is an individual SpliceGnss Object !
            spc_main_obj.table.loc[i_tabgrp,"fpath_inp"] = spc_obj
            spc_main_obj.table.loc[i_tabgrp,"fname"] = os.path.basename(spc_obj.table.iloc[0]["fpath_inp"])

        return spc_main_obj , spc_obj_lis_out


    def splice(self,rnxmod_dir_inp=None,handle_software='converto'):

        if rnxmod_dir_inp:
            rnxmod_dir = rnxmod_dir_inp
        else:
            rnxmod_dir = self.out_dir

        rinexmod_kwargs = {  # 'marker': 'TOTO',
            'compression': "gz",
            'longname': True,
            # 'sitelog': sitelogs,
            'force_rnx_load': True,
            'verbose': False,
            'tolerant_file_period': True,
            'full_history': True}

        for irow, row in self.table.iterrows():
            self.on_row_splice(irow,handle_software=handle_software)
            self.on_row_rinexmod(irow, rnxmod_dir, rinexmod_kwargs)
            if rnxmod_dir != self.out_dir:
                self.on_row_move_final(irow)

        return None

    def on_row_splice(self, irow, handle_software='converto'):

        if not self.table.loc[irow, 'ok_inp']:
            logger.warning("action on row skipped (input disabled): %s",
                           self.table.loc[irow, 'fname'])
            return None

        spc_row = self.table.loc[irow, 'fpath_inp']
        spc_row.decompress_table_batch()

        #### add a test here to be sure that only one epoch is inside

        tmp_dir_use = self.translate_path(self.tmp_dir)
        out_dir_use = self.translate_path(self.out_dir)

        fpath_inp_lst = list(spc_row.table['fpath_inp'])

        if handle_software == 'converto':
            frnxtmp, _ = arocnv.converter_run(fpath_inp_lst,
                                              tmp_dir_use,
                                              converter='converto',
                                              bin_options=['-cat'])
        elif handle_software == 'gfzrnx':
            frnxtmp, _ = arocnv.converter_run(fpath_inp_lst,
                                              tmp_dir_use,
                                              converter='gfzrnx',
                                              bin_options=['-f'])
        else:
            logger.error("wrong handle_software name: %s", handle_software)
            frnxtmp = None

        self.table.loc[irow, 'fpath_out'] = frnxtmp

        return frnxtmp