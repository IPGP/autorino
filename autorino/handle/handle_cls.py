#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 15:00:40 2024

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

# +++ Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger("autorino")
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])

BOLD_SRT = "\033[1m"
BOLD_END = "\033[0m"


class HandleGnss(arocmn.StepGnss):
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
        Initialize a HandleGnss object.

        This constructor initializes a HandleGnss object, which is used for handling
        GNSS data processing. It inherits from the StepGnss class.

        Parameters
        ----------
        out_dir : str
            The output directory for the processed files.
        tmp_dir : str
            The temporary directory for intermediate files.
        log_dir : str
            The directory for log files.
        inp_dir : str, optional
            The input directory for raw files. Default is None.
        epoch_range : EpochRange, optional
            The range of epochs to be processed. Default is None.
        site : dict, optional
            Information about the site. Default is None.
        session : dict, optional
            Information about the session. Default is None.
        options : dict, optional
            Additional options for the processing operation. Default is None.
        metadata : dict, optional
            Metadata for the processing operation. Default is None.
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

    def group_by_epochs(
        self,
        period="1d",
        rolling_period=False,
        rolling_ref=-1,
        round_method="floor",
        drop_epoch_rnd=False,
    ):
        """
        Group the data by epochs.

        This method groups the data in the table by epochs, rounding the epochs according
        to the specified period and method.
        It creates a main HandleGnss object and individual
        HandleGnss objects for each epoch group.

        Parameters
        ----------
        period : str, optional
            The period for rounding the epochs. Default is "1d".
        rolling_period : bool, optional
            Whether to use a rolling period for rounding. Default is False.
        rolling_ref : int, optional
            The reference for the rolling period. Default is -1.
        round_method : str, optional
            The method for rounding the epochs. Default is "floor".
        drop_epoch_rnd : bool, optional
            Whether to drop the temporary epoch_rnd column after grouping. Default is False.

        Returns
        -------
        tuple
            A tuple containing the main HandleGnss object and a list of individual
            HandleGnss objects for each epoch group.
        """

        epoch_rnd = arocmn.round_epochs(
            self.table["epoch_srt"],
            period=period,
            rolling_period=rolling_period,
            rolling_ref=rolling_ref,
            round_method=round_method,
        )

        self.table["epoch_rnd"] = epoch_rnd

        # get the main Handle object which will describe the final spliced RINEXs
        spc_main_obj_epoch_range = arocmn.EpochRange(
            np.min(epoch_rnd),
            np.max(epoch_rnd),
            period=period,
            round_method=round_method,
        )

        spc_main_obj = SpliceGnss(
            out_dir=self.out_dir,
            tmp_dir=self.tmp_dir,
            log_dir=self.log_dir,
            epoch_range=spc_main_obj_epoch_range,
            site=self.site,
            session=self.session,
        )

        # get individual Handle objects
        grps = self.table.groupby("epoch_rnd")

        spc_obj_lis_out = []

        spc_main_obj.table["ok_inp"] = False

        logger.info("%i epoch group(s) found", len(grps))

        for i_tabgrp, (t_tabgrp, tabgrp) in enumerate(grps):
            spc_obj = self.copy()

            if drop_epoch_rnd:  # remove the temporary epoch_rnd column
                tabgrp_bis = tabgrp.drop("epoch_rnd", axis=1)
            else:  # keep the temporary epoch_rnd column
                tabgrp_bis = pd.DataFrame(tabgrp)

            logger.info(
                "epoch group #%i: from %s for %s", i_tabgrp + 1, t_tabgrp, period
            )

            spc_obj.table = tabgrp_bis
            spc_obj.updt_eporng_tab()
            spc_obj_lis_out.append(spc_obj)

            # fill the main object with the individuals
            # then "fpath_inp" is an individual SpliceGnss Object !
            spc_main_obj.table.loc[i_tabgrp, "fpath_inp"] = spc_obj
            spc_main_obj.table.loc[i_tabgrp, "fname"] = os.path.basename(
                spc_obj.table.iloc[0]["fpath_inp"]
            )
            spc_main_obj.table.loc[i_tabgrp, "ok_inp"] = True

        return spc_main_obj, spc_obj_lis_out

    def feed_by_epochs(self, step_obj_feeder, mode="split", print_table=False):
        """
        For a HandleGnss object, with a predefined epoch range
        find the corresponding RINEX for splice/split in the step_obj_feeder StepGnss,
        which a list of possible RINEXs candidates for the splice/split operation

        Parameters
        ----------
        step_obj_feeder : StepGnss
            StepGnss object, which a list of possible RINEXs candidates
            for the splice/split operation

        mode : str
            split or splice
            if split: for fpath_inp, only one RINEX is returned
            (the need one for the split)
            if splice: for fpath_inp, a SpliceGnss object with several RINEXs is returned
            (all the needed ones for the splice)

        print_table : bool, optional
            If True, prints the tables for debugging purposes. Default is False.

        Returns
        -------
        None
        """
        if not (
            self.get_step_type(full_object_name=True)
            in ("HandleGnss", "SplitGnss", "SpliceGnss")
        ):
            logger.warning(
                "feed_by_epochs works with HandleGnss, SplitGnss, SpliceGnss objects only (%s here)",
                self.get_step_type(),
            )

        if print_table:
            logger.info("> Feeding table:")
            step_obj_feeder.print_table()
            logger.info("> Table to be feeded:")
            self.print_table()

        for irow, row in self.table.iterrows():

            if not self.mono_ok_check(
                irow,
                "feed_by_epochs",
                fname_custom=arocmn.iso_zulu_epoch(self.table.loc[irow, "epoch_srt"]),
            ):
                continue

            site = self.table.loc[irow, "site"]
            epo_srt_to_feed = self.table.loc[irow, "epoch_srt"]
            epo_end_to_feed = self.table.loc[irow, "epoch_end"]

            logger.info(
                ">>>> Feeding RINEXs for %s between %s & %s",
                site,
                arocmn.iso_zulu_epoch(epo_srt_to_feed),
                arocmn.iso_zulu_epoch(epo_end_to_feed),
            )
            if mode == "splice":
                epo_srt_bol = epo_srt_to_feed <= step_obj_feeder.table["epoch_srt"]
                # For Leica, the end epoch of the RINEX can be after the theoretical one...
                # we add one hour as margin, the splice software integrates the option
                # to stop at the right epoch
                m = self.epoch_range.extra_margin_splice()
                epo_end_bol = epo_end_to_feed + m >= step_obj_feeder.table["epoch_end"]

                # epo_end_bol = np.array([True] * len(epo_end_to_feed))
            elif mode == "split":
                epo_srt_bol = step_obj_feeder.table["epoch_srt"] <= epo_srt_to_feed
                epo_end_bol = step_obj_feeder.table["epoch_end"] >= epo_end_to_feed
            else:
                logger.error("wrong mode value (accept 'splice' or 'split'): %s", mode)
                raise ValueError

            epoch_bol = epo_srt_bol & epo_end_bol

            debug = False
            if debug:
                bol_stk = pd.DataFrame(
                    np.column_stack((epo_srt_bol, epo_end_bol, epoch_bol))
                )
                print(bol_stk.to_string())

            bol_sum = np.sum(epoch_bol)

            if bol_sum == 0:
                self.table.loc[irow, "ok_inp"] = False
                self.table.loc[irow, "fpath_inp"] = None
                logger.warning(
                    "no valid input RINEX between %s & %s",
                    arocmn.iso_zulu_epoch(epo_srt_to_feed),
                    arocmn.iso_zulu_epoch(epo_end_to_feed),
                )

            elif mode == "split":
                if bol_sum > 1:
                    logger.warning("%i (>1) RINEX found for feed: %s", bol_sum)

                rnxinp_row = step_obj_feeder.table.loc[epoch_bol].iloc[0]
                ###### can be improved !
                self.table.loc[irow, "ok_inp"] = True
                self.table.loc[irow, "fpath_inp"] = rnxinp_row["fpath_inp"]
                logger.info("found for feed: %s", rnxinp_row["fpath_inp"])

            elif mode == "splice":
                spc_obj = HandleGnss(
                    out_dir=self.out_dir,
                    tmp_dir=self.tmp_dir,
                    log_dir=self.log_dir,
                    epoch_range=None,
                    site={"site_id": site},
                    session=self.session,
                )

                spc_obj.table = step_obj_feeder.table.loc[epoch_bol].copy()
                spc_obj.updt_eporng_tab()
                spc_obj.updt_site_w_rnx_fname()

                logger.info("found for feed: %s", str(spc_obj))

                self.table.loc[irow, "ok_inp"] = True
                self.table.loc[irow, "fpath_inp"] = spc_obj
            else:  # should not happend
                self.table.loc[irow, "ok_inp"] = False
                self.table.loc[irow, "fpath_inp"] = None
                logger.warning(
                    "no valid input RINEX between %s & %s",
                    arocmn.iso_zulu_epoch(epo_srt_to_feed),
                    arocmn.iso_zulu_epoch(epo_end_to_feed),
                )

        return None

    def find_local_inp(self, return_as_step_obj=True, rnx3_regex=False):
        """
        Guess the paths and name of the local raw files based on the
        EpochRange and `inp_basename` attributes of the DownloadGnss object.

        Parameters
        ----------
        return_as_step_obj : bool, optional
            If True, returns the result as a StepGnss object.
            If False, returns a list of file paths. Default is True.
        rnx3_regex : bool, optional
            If True, uses a regex pattern for RINEX 3 filenames.
            If False, uses a wildcard pattern. Default is False.

        Returns
        -------
        StepGnss or list
            If return_as_step_obj is True, returns a StepGnss object populated with the found RINEX files.
            If return_as_step_obj is False, returns a list of found file paths.
        """

        local_paths_list = []

        for epoch in self.epoch_range.eporng_list(end_bound=True):
            # guess the potential local files
            local_dir_use = self.translate_path(self.inp_dir, epoch, make_dir=False)

            if rnx3_regex:
                patrn = self.site_id9 + conv.rinex_regex_long_name()[17:]
            else:
                patrn = ".*"

            local_paths_list_epo = utils.find_recursive(
                local_dir_use, pattern=patrn, regex=True
            )
            local_paths_list.extend(local_paths_list_epo)

        logger.info("nbr local files found: %s", len(local_paths_list))
        if return_as_step_obj:
            return arocmn.rnxs2step_obj(rnxs_lis_inp=local_paths_list)
        else:
            return local_paths_list

    def load_input_rnxs(self, input_mode, input_rinexs=None):
        """
        Get the input RINEX files for handeling (splice or split).

        This method retrieves the input RINEX files based on the specified input mode and input RINEXs.
        It can find local input files or use a provided input list.

        Parameters
        ----------
        input_mode : str
            The mode for finding input RINEX files. It can be:
            - "find": to find local input files.
            - "given": to use provided input RINEX files.
        input_rinexs : str or list or StepGnss
            The input RINEX files.
            Only useful for "given" mode.
            It can be:
            - A list of RINEX file paths.
            - An existing StepGnss object.

        Returns
        -------
        StepGnss or None
            A StepGnss object containing the input RINEX files, or None if an error occurs.
        """
        method_msg = "input method to handle RINEXs: "

        if input_mode == "find":
            # Find local RINEX files and convert them to a StepGnss object
            logger.debug(
                method_msg
                + "find local RINEX files and convert them to a StepGnss object"
            )
            stp_obj_rnxs_inp = self.find_local_inp(
                return_as_step_obj=True, rnx3_regex=True
            )
        elif input_mode == "given":
            if not input_rinexs:
                logger.error("input mode is 'given' but no input_rinexs provided")

            if utils.is_iterable(input_rinexs):
                # Convert a list of RINEX files to a StepGnss object
                logger.debug(
                    method_msg + "convert a RINEX files list to a StepGnss object"
                )
                stp_obj_rnxs_inp = arocmn.rnxs2step_obj(rnxs_lis_inp=input_rinexs)

            elif isinstance(input_rinexs, arocmn.StepGnss):
                # Use an existing StepGnss object containing the RINEX files
                logger.debug(
                    method_msg + "a StepGnss object containing the RINEX files"
                )
                stp_obj_rnxs_inp = input_rinexs
            else:
                # Log an error if the input_rinexs value is invalid
                logger.error(
                    "wrong input_rinexs value for the creation of a StepGnss object: %s",
                    input_rinexs,
                )
                return None
        else:
            # Log an error if the mode value is invalid
            logger.error(
                "wrong mode value: %s (only 'find' and 'given' are valid)", input_mode
            )
            return None

        return stp_obj_rnxs_inp

    def conv_softs_opts(
        self, irow, handle_software, conv_options_sup=[], conv_kwoptions_sup=dict()
    ):
        if handle_software == "converto":
            conv_kwoptions_basis = {
                "-st": self.table.loc[irow, "epoch_srt"].strftime("%Y%m%d%H%M%S"),
                "-e": self.table.loc[irow, "epoch_end"].strftime("%Y%m%d%H%M%S"),
            }
            conv_options_basis = ["-cat"]
        elif handle_software == "gfzrnx":
            duration = int(
                (
                    self.table.loc[irow, "epoch_end"]
                    - self.table.loc[irow, "epoch_srt"]
                ).total_seconds()
            )
            conv_kwoptions_basis = {
                "-epo_beg": self.table.loc[irow, "epoch_srt"].strftime("%Y%m%d_%H%M%S"),
                "-d": duration,
            }
            conv_options_basis = ["-f"]
        else:
            logger.critical("wrong handle_software value: %s", handle_software)
            raise ValueError

        conv_option_out = conv_options_basis + conv_options_sup
        conv_kwoption_out = {**conv_kwoptions_basis, **conv_kwoptions_sup}

        return conv_option_out, conv_kwoption_out
