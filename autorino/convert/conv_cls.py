#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  7 12:07:18 2023

@author: psakic
"""

import os
import re
import numpy as np
import datetime as dt
import dateutil
import docker
from pathlib import Path

from geodezyx import utils, operational

import autorino.common as arocmn
import autorino.convert as arocnv

from rinexmod import rinexmod_api

#### Import the logger
import logging

logger = logging.getLogger(__name__)
logger.setLevel("INFO")


class ConvertGnss(arocmn.StepGnss):
    def __init__(self, out_dir, tmp_dir, log_dir,
                 epoch_range=None,
                 site=None,
                 session=None,
                 sitelogs=None,
                 options=None):

        super().__init__(out_dir, tmp_dir, log_dir,
                         epoch_range=epoch_range,
                         site=site,
                         session=session,
                         options=options)

        ### temp dirs init
        self._init_tmp_dirs_paths()

        ### sitelog init
        if sitelogs:
            sitelogs_set = self.translate_path(sitelogs)
            self.sitelogs = rinexmod_api.sitelog_input_manage(sitelogs_set,
                                                              force=False)
        else:
            self.sitelogs = None

    ###############################################

    def convert(self, print_table=False, force=False,
                rinexmod_options={}):
        """
        "total action" method
        """
        logger.info("******** RAW > RINEX files conversion")

        tmp_dir_logs_use, _, _, _ = self.set_tmp_dirs_paths()

        if self.sitelogs:
            site4_list = arocnv.site_list_from_sitelogs(self.sitelogs)
        else:
            site4_list = []

        ### initialize the table as log
        self.set_table_log(out_dir=tmp_dir_logs_use)

        ### guess and deactivate existing local RINEX files
        if not force:
            self.guess_local_rnx_files()
            self.check_local_files()
            self.filter_ok_out()

        self.tmp_decmp_files = self.decompress()

        ### get a table with only the good files (ok_inp == True)
        # table_init_ok must be used only for the following statistics!
        table_init_ok = self.filter_purge()
        n_ok_inp = (self.table['ok_inp']).sum()
        n_not_ok_inp = np.logical_not(self.table['ok_inp']).sum()

        logger.info("%6i files will be converted, %6i files are excluded",
                    n_ok_inp, n_not_ok_inp)

        if print_table:
            self.print_table()

        ######################### START THE LOOP ##############################
        for irow, row in self.table.iterrows():
            fraw = Path(row['fpath_inp'])
            ext = fraw.suffix.lower()

            if not self.table.loc[irow, 'ok_inp'] and self.table.loc[irow, 'ok_out']:
                logger.info("conversion skipped (output already exists): %s", fraw)
                continue
            if not self.table.loc[irow, 'ok_inp']:
                logger.warning("conversion skipped (something went wrong): %s", fraw)
                continue

            logger.info("***** input raw file for conversion: %s",
                        fraw.name)

            _, tmp_dir_unzipped_use, tmp_dir_converted_use, tmp_dir_rinexmoded_use = self.set_tmp_dirs_paths()

            ### since the site code from fraw can be poorly formatted
            # we search it w.r.t. the sites from the sitelogs
            site = arocnv.site_search_from_list(fraw,
                                                site4_list)

            ### do a first converter selection by removing odd files 
            conve = arocnv.select_conv_odd_file(fraw)

            logger.info("extension/converter: %s/%s", ext, conve)

            if not conve:
                logger.info("file skipped, no converter found: %s", fraw)
                self.table.loc[irow, 'note'] = "no converter found"
                self.table.loc[irow, 'ok_inp'] = False
                self.write_in_table_log(self.table.loc[irow])

            ### a function to stop the docker containers running for too long
            # (for trimble conversion)
            arocnv.stop_long_running_containers()

            #############################################################
            ###### CONVERSION
            frnxtmp = self.on_row_convert(irow, tmp_dir_converted_use,
                                          converter_inp=conve)
            self.tmp_rnx_files.append(frnxtmp)  ### list for final remove
            ### NO MORE EXCEPTION HERE FOR THE MOMENT !!!!!

            #############################################################
            ###### RINEXMOD
            rinexmod_kwargs = rinexmod_options.copy()
            rinexmod_kwargs.update({'marker':site,
                                    'sitelog':self.sitelogs})

            self.on_row_rinexmod(irow, tmp_dir_rinexmoded_use, rinexmod_kwargs)
            ### NO MORE EXCEPTION HERE FOR THE MOMENT !!!!!

            #############################################################
            ###### FINAL MOVE
            self.on_row_move_final(irow)
            ### NO MORE EXCEPTION HERE FOR THE MOMENT !!!!!

        #### remove temporary files

        self.remove_tmp_files()

        return None

    #               _   _
    #     /\       | | (_)
    #    /  \   ___| |_ _  ___  _ __  ___    ___  _ __    _ __ _____      _____
    #   / /\ \ / __| __| |/ _ \| '_ \/ __|  / _ \| '_ \  | '__/ _ \ \ /\ / / __|
    #  / ____ \ (__| |_| | (_) | | | \__ \ | (_) | | | | | | | (_) \ V  V /\__ \
    # /_/    \_\___|\__|_|\___/|_| |_|___/  \___/|_| |_| |_|  \___/ \_/\_/ |___/
    #

    def on_row_convert(self, irow, out_dir_inp, converter_inp,
                       table_col = 'fpath_inp'):

        """
        "on row" method

        for each row of the table, convert the 'table_col' entry,
        typically 'table_col' file
        """

        if not self.table.loc[irow, 'ok_inp']:
            logger.warning("action on row skipped (input disabled): %s",
                           self.table.loc[irow, 'fname'])
            return None

        frnxtmp, _ = arocnv.converter_run(self.table.loc[irow, table_col],
                                          out_dir_inp,
                                          converter=converter_inp)
        if frnxtmp:
            ### update table if things go well
            self.table.loc[irow, 'fpath_out'] = frnxtmp
            epo_srt_ok, epo_end_ok = operational.rinex_start_end(frnxtmp)
            self.table.loc[irow, 'epoch_srt'] = epo_srt_ok
            self.table.loc[irow, 'epoch_end'] = epo_end_ok
            self.table.loc[irow, 'ok_out'] = True
        else:
            ### update table if things go wrong
            self.table.loc[irow, 'ok_out'] = False
        return frnxtmp