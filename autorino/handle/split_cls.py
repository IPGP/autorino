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

# Create a logger object.
import logging

logger = logging.getLogger(__name__)


#   _____       _ _ _
#  / ____|     | (_) |
# | (___  _ __ | |_| |_
#  \___ \| '_ \| | | __|
#  ____) | |_) | | | |_
# |_____/| .__/|_|_|\__|
#        | |
#        |_|


class SplitGnss(arocmn.StepGnss):
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

    def split(self, handle_software='converto', rinexmod_options={}):
        """
        "total action" method
        """

        self.set_tmp_dirs_paths()

        for irow, row in self.table.iterrows():
            fdecmptmp , _ = self.on_row_decompress(irow)
            self.tmp_decmp_files.append(fdecmptmp)

            frnx_splited = self.on_row_split(irow, self.tmp_dir_converted,
                                             handle_software=handle_software)
            if not self.table.loc[irow, 'fpath_out']:
                logger.error("unable to split %s, skip",
                             self.table.loc[irow])
                continue

            self.tmp_rnx_files.append(frnx_splited)

            self.on_row_rinexmod(irow, self.tmp_dir_rinexmoded, rinexmod_options)
            if self.tmp_dir_rinexmoded != self.out_dir:
                self.on_row_move_final(irow)

        self.remove_tmp_files()

        return None


    def on_row_split(self, irow, out_dir = None, table_col='fpath_inp',
                     handle_software='converto'):
        """
        "on row" method

        for each row of the table, split the 'table_col' entry,
        typically 'fpath_inp' file
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

        frnx_inp = self.table.loc[irow, table_col]

        if handle_software == 'converto':
            conv_kwoptions = {'-st': self.table.loc[irow, 'epoch_srt'].strftime('%Y%m%d%H%M%S'),
                              '-e': self.table.loc[irow, 'epoch_end'].strftime('%Y%m%d%H%M%S')}
            conv_options = []
        elif handle_software == 'gfzrnx':
            duration = int((self.table.loc[irow, 'epoch_end'] - self.table.loc[irow, "epoch_srt"]).total_seconds())
            conv_kwoptions = {'-epo_beg': self.table.loc[irow, 'epoch_srt'].strftime('%Y%m%d_%H%M%S'),
                              '-d': duration}
            conv_options = ['-f']

        else:
            logger.error('wrong handle_software value: %s', handle_software)
            raise ValueError

        try:
            frnxtmp, _ = arocnv.converter_run(frnx_inp,
                                              out_dir_use,
                                              converter=handle_software,
                                              bin_options=conv_options,
                                              bin_kwoptions=conv_kwoptions)

            self.table.loc[irow, 'fpath_out'] = frnxtmp
            self.table.loc[irow, 'ok_out'] = True
        except Exception as e:
            logger.error(e)
            self.table.loc[irow, 'ok_out'] = False
            self.write_in_table_log(self.table.loc[irow])
            frnxtmp = None
            raise e

        return frnxtmp