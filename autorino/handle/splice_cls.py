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
                 options=None,
                 sitelogs=sitelogs):

        super().__init__(out_dir, tmp_dir, log_dir,
                         epoch_range=epoch_range,
                         site=site,
                         session=session,
                         options=options,
                         sitelogs=sitelogs)

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

        spc_main_obj.table["ok_inp"] = False

        for i_tabgrp, (t_tabgrp, tabgrp) in enumerate(grps):
            spc_obj = self.copy()

            if drop_epoch_rnd: ### remove the temporary epoch_rnd column
                tabgrp_bis = tabgrp.drop('epoch_rnd', axis=1)
            else: ### keep the temporary epoch_rnd column
                tabgrp_bis = pd.DataFrame(tabgrp)

            spc_obj.table = tabgrp_bis
            spc_obj.update_epoch_range_from_table()
            spc_obj_lis_out.append(spc_obj)

            # fill the main object with the individuals
            # then "fpath_inp" is an individual SpliceGnss Object !
            spc_main_obj.table.loc[i_tabgrp,"fpath_inp"] = spc_obj
            spc_main_obj.table.loc[i_tabgrp,"fname"] = os.path.basename(spc_obj.table.iloc[0]["fpath_inp"])
            spc_main_obj.table.loc[i_tabgrp,"ok_inp"] = True

        return spc_main_obj , spc_obj_lis_out


    def splice(self, handle_software='converto', rinexmod_options={}):
        """
        "total action" method
        """

        self.set_tmp_dirs_paths()

        for irow, row in self.table.iterrows():
            self.on_row_splice(irow,
                               self.tmp_dir_converted,
                               handle_software=handle_software)
            if not self.table.loc[irow, 'fpath_out']:
                logger.error("unable to splice %s, skip",
                             self.table.loc[irow])
                continue

            self.on_row_rinexmod(irow,
                                 self.tmp_dir_rinexmoded,
                                 rinexmod_kwargs=rinexmod_options)
            if self.tmp_dir_rinexmoded != self.out_dir:
                self.on_row_move_final(irow,
                                       self.out_dir)

        self.remove_tmp_files()

        return None

    def on_row_splice(self, irow, out_dir = None, table_col = 'fpath_inp', handle_software='converto'):
        """
        "on row" method

        for each row of the table, splice the 'table_col' entry,
        typically 'fpath_inp' file

        in the splice case, fpath_inp in another SpliceGnss object,
        containing the RINEXs to splice
        """

        if not self.table.loc[irow, 'ok_inp']:
            logger.warning("action on row skipped (input disabled): %s",
                           self.table.loc[irow, 'epoch_srt'])
            return None

        # definition of the output directory (after the action)
        if out_dir:
            out_dir_use = out_dir
        elif hasattr(self, 'tmp_dir_converted'):
            out_dir_use = self.tmp_dir_converted
        else:
            out_dir_use = self.tmp_dir

        spc_row = self.table.loc[irow, 'fpath_inp']

        if not isinstance(spc_row,SpliceGnss):
            logger.error("the fpath_inp is not a SpliceGnss object: %s", self.table.loc[irow])
            frnx_spliced = None
        else:
            ### it is not the current object inputs which are decompressed, but the row sub object's ones
            spc_row.tmp_decmp_files , _ = spc_row.decompress()

            #### add a test here to be sure that only one epoch is inside

            tmp_dir_use = self.translate_path(self.tmp_dir)
            out_dir_use = self.translate_path(self.out_dir)

            fpath_inp_lst = list(spc_row.table['fpath_inp'])

            if handle_software == 'converto':
                frnx_spliced, _ = arocnv.converter_run(fpath_inp_lst,
                                                  tmp_dir_use,
                                                  converter='converto',
                                                  bin_options=['-cat'])
            elif handle_software == 'gfzrnx':
                frnx_spliced, _ = arocnv.converter_run(fpath_inp_lst,
                                                  tmp_dir_use,
                                                  converter='gfzrnx',
                                                  bin_options=['-f'])
            else:
                logger.error("wrong handle_software name: %s", handle_software)
                frnx_spliced = None

        self.table.loc[irow, 'fpath_out'] = frnx_spliced

        ### it is not the current object temps which are removed, but the row sub object's ones
        spc_row.remove_tmp_files()

        return frnx_spliced