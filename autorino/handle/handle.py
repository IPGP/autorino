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


class HandleGnss(arocmn.StepGnss):
    def __init__(self, out_dir, tmp_dir, log_dir,
                 epoch_range,
                 site=None,
                 session=None):

        super().__init__(out_dir, tmp_dir, log_dir,
                         epoch_range,
                         site=site,
                         session=session)

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

        # get individual Handle objects
        grps = self.table.groupby('epoch_rnd')

        stp_obj_lis_out = []

        for tgrp, tabgrp in grps:
            hdl_obj = self.copy()

            if drop_epoch_rnd:
                tabgrp_bis = tabgrp.drop('epoch_rnd', axis=1)
            else:
                tabgrp_bis = pd.DataFrame(tabgrp)
            hdl_obj.table = tabgrp_bis
            hdl_obj.update_epoch_range_from_table()
            stp_obj_lis_out.append(hdl_obj)

        # get the main Handle object which will describe the final spliced RINEXs
        hdl_main_obj = self.copy()

        # hdl_main_obj_epoch_range = arocmn.EpochRange(np.min(epoch_rnd),
        #                                              np.max(epoch_rnd),
        #                                              period=period,
        #                                              round_method=round_method)
        #
        # hdl_main_obj = HandleGnss(out_dir=self.out_dir,
        #                           tmp_dir=self.tmp_dir,
        #                           log_dir=self.log_dir,
        #                           epoch_range=hdl_main_obj_epoch_range,
        #                           site=self.site,
        #                           session=self.session)
        return stp_obj_lis_out

    def splice(self):
        ### divide_by_epochs will create several HandleGnss objects
        hdl_objs_lis = self.divide_by_epochs()

        for hdl in hdl_objs_lis:
            hdl._splice_mono()

    def splice_mono(self, handle_software='converto'):
        #### add a test here to be sure that only one epoch is inside
        fpath_inp_lst = list(self.table['fpath_inp'])

        tmp_dir_use = self.translate_path(self.tmp_dir)
        out_dir_use = self.translate_path(self.out_dir)

        if handle_software == 'converto':
            frnxtmp, _ = arocnv.converter_run(fpath_inp_lst,
                                              tmp_dir_use,
                                              'converto',
                                              bin_options=['-cat'])
        elif handle_software == 'gfzrnx':
            frnxtmp, _ = arocnv.converter_run(fpath_inp_lst,
                                              tmp_dir_use,
                                              'gfzrnx',
                                              bin_options=['-f'])


    def find_rnxs_for_split(self, hdl_store):
        for irow, row in self.table.iterrows():
            epo_srt = np.datetime64(self.table.loc[irow, 'epoch_srt'])
            epo_end = np.datetime64(self.table.loc[irow, 'epoch_end'])

            epoch_srt_bool = hdl_store.table['epoch_srt'] <= epo_srt
            epoch_end_bool = hdl_store.table['epoch_end'] >= epo_end

            epoch_bool = epoch_srt_bool & epoch_end_bool

            if epoch_bool.sum() == 0:
                print("no")
                self.table.loc[irow, 'ok_inp'] = False
                continue
            elif epoch_bool.sum() > 1:
                print("> 1, keep first")
                rnxinp_row = hdl_store.table.loc[epoch_bool].iloc[0]
            else:
                rnxinp_row = hdl_store.table.loc[epoch_bool].squeeze()

            self.table.loc[irow, 'fpath_inp'] = rnxinp_row['fpath_inp']
            self.table.loc[irow, 'ok_inp'] = True