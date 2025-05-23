#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 20/05/2025 20:26:56

@author: psakic
"""




# Create a logger object.
import os
import time

import numpy as np
import pandas as pd
from pathlib import Path

from geodezyx import utils, conv

import autorino.common as arocmn
import autorino.convert as arocnv
import autorino.handle.handle_cls as arohdlcls

# +++ Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger("autorino")
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])

BOLD_SRT = "\033[1m"
BOLD_END = "\033[0m"


#   _____       _ _
#  / ____|     | (_)
# | (___  _ __ | |_  ___ ___
#  \___ \| '_ \| | |/ __/ _ \
#  ____) | |_) | | | (_|  __/
# |_____/| .__/|_|_|\___\___|
#        | |
#        |_|


class SpliceGnss(arohdlcls.HandleGnss):
    def __init__(
        self,
        out_dir,
        tmp_dir,
        log_dir,
        inp_dir=None,
        inp_file_regex=None,
        epoch_range=None,
        site=None,
        session=None,
        options=None,
        metadata=None,
    ):
        """
        Initialize a SpliceGnss object.

        This constructor initializes a SpliceGnss object, which is used for handling
        the splicing of RINEX files. It inherits from the HandleGnss class.

        Parameters
        ----------
        out_dir : str
            The output directory for the spliced RINEX files.
        tmp_dir : str
            The temporary directory for intermediate files.
        log_dir : str
            The directory for log files.
        inp_dir : str, optional
            The input directory for raw files. Default is None.
        inp_file_regex : str, optional
            The regular expression for filtering input files. Default is None.
        epoch_range : EpochRange, optional
            The range of epochs to be processed. Default is None.
        site : dict, optional
            Information about the site. Default is None.
        session : dict, optional
            Information about the session. Default is None.
        options : dict, optional
            Additional options for the splicing operation. Default is None.
        metadata : dict, optional
            Metadata for the splicing operation. Default is None.
        """

        super().__init__(
            out_dir=out_dir,
            tmp_dir=tmp_dir,
            log_dir=log_dir,
            inp_dir=inp_dir,
            inp_file_regex=inp_file_regex,
            epoch_range=epoch_range,
            site=site,
            session=session,
            options=options,
            metadata=metadata,
        )

    def splice(
        self,
        input_mode="find",
        input_rinexs=None,
        handle_software="converto",
        rinexmod_options=None,
        verbose=False,
        force=False,
    ):
        """
        Splice RINEX files.

        This method splices RINEX files based on the provided input. It can find local input files,
        convert a list of RINEX files to a StepGnss object, or use an existing StepGnss object.
        The splicing operation is performed using the specified software and options.

        Parameters
        ----------
        input_mode : str, optional
            The mode for finding input RINEX files. It can be:
            - "find": to find local input files.
            - "given": to use provided input RINEX files.
            Default is "find".
        input_rinexs : str or list or StepGnss, optional
            The input RINEX files. It can be:
            - A list of RINEX file paths.
            - An existing StepGnss object.
            Default is None.
        handle_software : str, optional
            The software to use for handling the RINEX files. Default is "converto".
        rinexmod_options : dict, optional
            Additional options for the RINEX modification. Default is None.
        verbose : bool, optional
            If True, prints the table for debugging purposes. Default is False.
        force : bool, optional
            If True, forces the splicing operation. Default is False.

        Returns
        -------
        None
        """
        # set the log file
        self.set_logfile()

        # Log the start of the splicing operation
        logger.info(BOLD_SRT + ">>>>>> Splicing RINEX files" + BOLD_END)

        # set ok_inp to True per default
        self.table["ok_inp"] = True

        # generate the potential local files
        self.guess_local_rnx()
        # tests if the output local files are already there
        self.check_local_files("out")
        # switch ok_inp to False if the output files are already there
        self.filter_ok_out()

        # if force is True, force the splicing operation
        if force:
            self.force("splice")

        # Find the input RINEX files
        stp_obj_rnxs_inp = self.load_input_rnxs(input_mode, input_rinexs)
        # Feed the epochs for splicing
        self.feed_by_epochs(stp_obj_rnxs_inp, mode="splice", print_table=verbose)

        # Perform the core splicing operation
        self.splice_core(
            handle_software=handle_software, rinexmod_options=rinexmod_options
        )

        # close the log file
        self.close_logfile()

        return None

    def splice_core(
        self, handle_software="converto", rinexmod_options=None, rm_inp_files=False
    ):
        """
        Perform the core splicing operation.

        This method handles the core splicing operation for RINEX files. It iterates over each row
        in the table, performs the splicing operation using the specified software, and applies
        RINEX modifications if necessary. Temporary files are removed after the operation.

        Parameters
        ----------
        handle_software : str, optional
            The software to use for handling the RINEX files. Default is "converto".
        rinexmod_options : dict, optional
            Additional options for the RINEX modification. Default is None.

        Returns
        -------
        None
        """

        self.set_tmp_dirs()

        for irow, row in self.table.iterrows():
            if not self.mono_ok_check(
                irow,
                "splice",
                fname_custom=arocmn.iso_zulu_epoch(self.table.loc[irow, "epoch_srt"]),
            ):
                continue

            logger.info(
                ">>>> Splicing %s between %s and %s",
                self.table.loc[irow, "site"],
                arocmn.iso_zulu_epoch(self.table.loc[irow, "epoch_srt"]),
                arocmn.iso_zulu_epoch(self.table.loc[irow, "epoch_end"]),
            )

            self.mono_splice(
                irow, self.tmp_dir_converted, handle_software=handle_software
            )

            if not self.table.loc[irow, "ok_out"] and self.table.loc[irow, "ok_inp"]:
                # print this only if ok_inp is True, i.e. the file should have been converted
                logger.error("unable to splice\n%s", self.table.loc[irow].to_string())
                continue

            self.mono_rinexmod(
                irow, self.tmp_dir_rinexmoded, rinexmod_options=rinexmod_options
            )

            # if rm_inp_files:
            # IMPLEMENT ME !!!!!!

            if self.tmp_dir_rinexmoded != self.out_dir:
                self.mono_mv_final(irow, self.out_dir)

        self.remov_tmp_files()
        return None

    def mono_splice(
        self, irow, out_dir=None, table_col="fpath_inp", handle_software="converto"
    ):
        """
        "on row" method

        for each row of the table, splice the 'table_col' entry,
        typically 'fpath_inp' file

        in the splice case, fpath_inp in another SpliceGnss object,
        containing the RINEXs to splice
        """

        if not self.mono_ok_check(
            irow,
            "splice (mono)",
            fname_custom=arocmn.iso_zulu_epoch(self.table.loc[irow, "epoch_srt"]),
            switch_ok_out_false=True,
        ):
            return None

        # definition of the output directory (after the action)
        if out_dir:
            out_dir_main_use = out_dir
        elif hasattr(self, "tmp_dir_converted"):
            out_dir_main_use = self.tmp_dir_converted
        else:
            out_dir_main_use = self.tmp_dir

        spc_row = self.table.loc[irow, "fpath_inp"]
        if not isinstance(spc_row, arohdlcls.HandleGnss):
            logger.error(
                f"fpath_inp is not a HandleGnss object: {self.table.loc[irow]:}"
            )
            frnx_spliced = None
        else:
            ### it is not the current object inputs which are decompressed, but the row sub object's ones
            spc_row.tmp_decmp_files, _ = spc_row.decompress()

            #### add a test here to be sure that only one epoch is inside
            out_dir_use = self.translate_path(
                out_dir_main_use, self.table.loc[irow, "epoch_srt"]
            )

            fpath_inp_lst = list(spc_row.table["fpath_inp"])

            conv_options, conv_kwoptions = self.conv_softs_opts(
                irow, handle_software=handle_software, conv_options_sup=["-cat"]
            )
            try:
                time.sleep(1)
                frnx_spliced, _ = arocnv.converter_run(
                    fpath_inp_lst,
                    out_dir_use,
                    converter=handle_software,
                    bin_options=conv_options,
                    bin_kwoptions=conv_kwoptions,
                )
            except Exception as e:
                logger.error("Error for: %s", fpath_inp_lst)
                logger.error("Exception raised: %s", e)
                frnx_spliced = None

        if frnx_spliced:
            self.table.loc[irow, "ok_out"] = True
            self.table.loc[irow, "fpath_out"] = frnx_spliced
        else:
            self.table.loc[irow, "ok_out"] = False
            # raise e

        ### it is not the current object temps which are removed, but the row sub object's ones
        spc_row.remov_tmp_files()

        return frnx_spliced


