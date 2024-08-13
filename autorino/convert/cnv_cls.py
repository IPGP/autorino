#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  7 12:07:18 2023

@author: psakic
"""

from pathlib import Path

import numpy as np

import autorino.common as arocmn
import autorino.convert as arocnv
from geodezyx import operational

#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger(__name__)
logger.setLevel(aroenv.aro_env_dict["general"]["log_level"])

BOLD_SRT = '\033[1m'
BOLD_END = '\033[0m'

class ConvertGnss(arocmn.StepGnss):
    """
    A class used to represent the GNSS conversion process.

    This class inherits from the StepGnss class and is used to handle the conversion of GNSS data.

    Attributes
    ----------
    out_dir : str
        The directory where the output of the conversion should be stored.
    tmp_dir : str
        The directory where temporary files during the conversion process should be stored.
    log_dir : str
        The directory where log files should be stored.
    epoch_range : tuple, optional
        A tuple containing the start and end epochs for the conversion process.
    site : str, optional
        The site for which the conversion process should be performed.
    session : str, optional
        The session for which the conversion process should be performed.
    options : dict, optional
        A dictionary containing any additional options for the conversion process.
    metadata : str or list, optional
        The metadata to be included in the converted RINEX files
        Possible inputs are:
        * list of string (sitelog file paths),
        * single string (single sitelog file path)
        * single string (directory containing the sitelogs)
        * list of MetaData objects
        * single MetaData object

    Methods
    -------
    __init__(self, out_dir, tmp_dir, log_dir, epoch_range=None, site=None, session=None, options=None, metadata=None)
        Initializes the ConvertGnss class with the specified parameters.
    """

    def __init__(
        self,
        out_dir,
        tmp_dir,
        log_dir,
        epoch_range=None,
        site=None,
        session=None,
        options=None,
        metadata=None,
    ):
        """
        Initializes the ConvertGnss class with the specified parameters.

        Parameters
        ----------
        out_dir : str
            The directory where the output of the conversion should be stored.
        tmp_dir : str
            The directory where temporary files during the conversion process should be stored.
        log_dir : str
            The directory where log files should be stored.
        epoch_range : tuple, optional
            A tuple containing the start and end epochs for the conversion process.
        site : str, optional
            The site for which the conversion process should be performed.
        session : str, optional
            The session for which the conversion process should be performed.
        options : dict, optional
            A dictionary containing any additional options for the conversion process.
        metadata : str or list, optional
            The metadata to be included in the converted RINEX files
            Possible inputs are:
            * list of string (sitelog file paths),
            * single string (single sitelog file path)
            * single string (directory containing the sitelogs)
            * list of MetaData objects
            * single MetaData object
        """
        super().__init__(
            out_dir,
            tmp_dir,
            log_dir,
            epoch_range=epoch_range,
            site=site,
            session=session,
            options=options,
            metadata=metadata,
        )

    ###############################################

    def convert(self, verbose=False, force=False, rinexmod_options=None):
        """
        "total action" method

        Executes the total conversion process for GNSS data.

        This method handles the entire conversion process for GNSS data.
        It sets up temporary directories, guesses and deactivates existing local RINEX files, decompresses files,
        filters and converts input files, applies rinexmod options, and finally moves the converted files to
        the final directory.
        It also handles logging and error checking throughout the process.

        Parameters
        ----------
        verbose : bool, optional
            If True, prints the conversion table. Default is False.
        force : bool, optional
            If True, forces the conversion even if output files already exist. Default is False.
        rinexmod_options : dict, optional
            A dictionary containing options for the rinexmod process. If not specified, default options are used.

        Returns
        -------
        None
        """

        logger.info(BOLD_SRT  + ">>>>>>>>> RAW > RINEX files conversion" + BOLD_END)

        # here the None to dict is necessary, because we use a defaut rinexmod_options bellow
        if rinexmod_options is None:
            rinexmod_options = {}

        if self.options.get("force") or force:
            force_use = True
            logger.info("Force conversion is enabled.")
        else:
            force_use = False

        self.set_tmp_dirs()
        self.clean_tmp_dirs()
        # other tmps subdirs come also later in the loop
        self.set_translate_dict()
        # others translate dict updates will come in the loop

        if self.metadata:
            site4_list, site9_list = arocnv.site_list_from_metadata(self.metadata)
        else:
            site4_list, site9_list = [], []

        ### initialize the table as log
        self.set_table_log(out_dir=self.tmp_dir_logs)

        ### guess and deactivate existing local RINEX files
        self.guess_local_rnx()  # generate the potential local files
        self.check_local_files('out')  # tests if the output local files are already there
        self.check_local_files('inp')  # tests if the input local files are already there

        if force_use:
            self.table["ok_inp"] = True
            self.table["note"] = "force_convert"
        else:
            prv_tbl_df = arocmn.load_previous_tables(self.tmp_dir_logs)
            # Filter previous tables stored in log_dir
            if len(prv_tbl_df) > 0:
                self.filter_previous_tables(prv_tbl_df)
            self.filter_ok_out()

        self.tmp_decmp_files, _ = self.decompress()

        # get a table with only the good files (ok_inp == True)
        # table_init_ok must be used only for the following statistics!
        self.table_ok_cols_bool()
        table_init_ok = self.filter_purge()

        n_tot_inp = len(self.table["ok_inp"])
        n_ok_inp = (self.table["ok_inp"]).sum()
        n_not_ok_inp = np.logical_not(self.table["ok_inp"]).sum()

        logger.info(
            "%5i/%5i files will be converted, %5i/%5i files are excluded",
            n_ok_inp,
            n_tot_inp,
            n_not_ok_inp,
            n_tot_inp
        )

        if verbose:
            self.print_table()

        ######################### START THE LOOP ##############################
        for irow, row in self.table.iterrows():
            fraw = Path(self.table.loc[irow, "fpath_inp"])
            ext = fraw.suffix.lower()

            if not self.table.loc[irow, "ok_inp"] and self.table.loc[irow, "ok_out"]:
                logger.info("conversion skipped (output already exists): %s", fraw)
                continue
            # +++ the test bellow conflicts the Force option
            #elif self.table.loc[irow, "ok_inp"] and self.table.loc[irow, "ok_out"]:
            #    logger.info(
            #        "conversion skipped (already converted in a previous run): %s", fraw
            #    )
            #    continue
            elif not self.table.loc[irow, "ok_inp"]:
                logger.warning("conversion skipped (something went wrong): %s", fraw)
                continue
            else:
                pass

            logger.info(">>> input raw file for conversion: %s", fraw.name)

            ###########################################################################
            # change the site_id here is a very bad idea, it f*cks the outdir 240605
            # in fact not, because of the new IGS update (9 char in sitlog)
            # it should not be a pb anymore

            # +++ since the site code from fraw can be poorly formatted
            # we search it w.r.t. the sites from the metadata
            # we update the table row and the translate_dic (necessary for the output dir)
            self.on_row_site_upd(irow, site4_list)
            self.site_id = self.table.loc[irow, "site"]  # for the output dir

            self.set_translate_dict()
            ###########################################################################

            # ++ do a first converter selection by identifying odd files
            converter_name_use = arocnv.select_conv_odd_file(fraw)

            logger.info("extension/converter: %s/%s", ext, converter_name_use)

            if not converter_name_use:
                logger.info("file skipped, no converter found: %s", fraw)
                self.table.loc[irow, "note"] = "no converter found"
                self.table.loc[irow, "ok_inp"] = False
                self.write_in_table_log(self.table.loc[irow])

            # ++ a function to stop the docker containers running for too long
            # (for trimble conversion)
            arocnv.stop_old_docker()

            #############################################################
            # +++++ CONVERSION
            frnxtmp = self.on_row_convert(
                irow, self.tmp_dir_converted, converter_inp=converter_name_use
            )
            self.tmp_rnx_files.append(frnxtmp)  # list for final remove

            #############################################################
            # +++++ RINEXMOD
            rinexmod_options_use = rinexmod_options.copy()

            debug_print_rinexmod_options = False
            if debug_print_rinexmod_options:
                logger.debug("input options for rinexmod: %s", rinexmod_options_use)

            # if "marker" is in rinexmod_options_use keys, use it, else use site
            if "marker" in rinexmod_options_use.keys():
                marker_use = rinexmod_options_use["marker"]
            else:
                marker_use = self.table.loc[irow, "site"]

            rinexmod_options_use.update(
                {"marker": marker_use, "sitelog": self.metadata}
            )
            if debug_print_rinexmod_options:
                logger.debug("final options for rinexmod: %s", rinexmod_options_use)

            self.on_row_rinexmod(
                irow, self.tmp_dir_rinexmoded, rinexmod_options=rinexmod_options_use
            )

            #############################################################
            # +++++ FINAL MOVE
            self.on_row_mv_final(irow)

        # ++++ remove temporary files
        self.remov_tmp_files()

        return None

    #               _   _
    #     /\       | | (_)
    #    /  \   ___| |_ _  ___  _ __  ___    ___  _ __    _ __ _____      _____
    #   / /\ \ / __| __| |/ _ \| '_ \/ __|  / _ \| '_ \  | '__/ _ \ \ /\ / / __|
    #  / ____ \ (__| |_| | (_) | | | \__ \ | (_) | | | | | | | (_) \ V  V /\__ \
    # /_/    \_\___|\__|_|\___/|_| |_|___/  \___/|_| |_| |_|  \___/ \_/\_/ |___/
    #

    def on_row_convert(
        self, irow, out_dir=None, converter_inp="auto", table_col="fpath_inp"
    ):
        """
        "on row" method

        Converts the 'table_col' entry for each row of the table.

        This method is applied to each row of the table. It converts the 'table_col' entry, typically a file.
        The conversion is performed using the specified converter.
        If no converter is specified, an automatic converter is used.
        The output of the conversion is stored in the specified output directory.
        If no output directory is specified, the output is stored in the temporary directory.

        Parameters
        ----------
        irow : int
            The index of the row in the table to be converted.
        out_dir : str, optional
            The directory where the output of the conversion should be stored. If not specified, the output is stored
            in the temporary directory.
        converter_inp : str, optional
            The converter to be used for the conversion. If not specified, an automatic converter is used.
        table_col : str, optional
            The column in the table that should be converted. Typically, this is a file. Default is 'fpath_inp'.

        Returns
        -------
        str
            The path of the converted file.
        """

        if not self.table.loc[irow, "ok_inp"]:
            logger.warning(
                "action on row skipped (input disabled): %s",
                self.table.loc[irow, "fname"],
            )
            return None

        # definition of the output directory (after the action)
        if out_dir:
            out_dir_use = out_dir
        elif hasattr(self, "tmp_dir_converted"):
            out_dir_use = self.tmp_dir_converted
        else:
            out_dir_use = self.tmp_dir

        try:
            frnxtmp, _ = arocnv.converter_run(
                self.table.loc[irow, table_col], out_dir, converter=converter_inp
            )
        except Exception as e:
            logger.error("something went wrong for %s", self.table.loc[irow, table_col])
            logger.error("Exception raised: %s", e)
            frnxtmp = None

        if frnxtmp:
            ### update table if things go well
            self.table.loc[irow, "ok_out"] = True
            self.table.loc[irow, "fpath_out"] = frnxtmp
            epo_srt_ok, epo_end_ok = operational.rinex_start_end(frnxtmp)
            self.table.loc[irow, "epoch_srt"] = epo_srt_ok
            self.table.loc[irow, "epoch_end"] = epo_end_ok
        else:
            ### update table if things go wrong
            self.table.loc[irow, "ok_out"] = False
        return frnxtmp

    def on_row_site_upd(self, irow, metadata_or_sites_list_inp, force=False):
        """
        Updates the 'site' entry for each row of the table.

        This method is applied to each row of the table. It checks if the 'site' entry is defined.
        If it is not defined or if the 'force' parameter is set to True, it updates the 'site' entry.
        The update is performed by searching the site from a list of sites or metadata.
        If the 'site' entry is already defined and 'force' is not set to True, it sets the 'site' entry to 'XXXX00XXX'.

        Parameters
        ----------
        irow : int
            The index of the row in the table to be updated.
        metadata_or_sites_list_inp : list
            A list of sites or metadata from which the site should be searched.
        force : bool, optional
            If True, forces the update of the 'site' entry even if it is already defined. Default is False.

        Returns
        -------
        str
            The updated 'site' entry.
        """
        val_def = arocmn.is_ok(self.table.loc[irow, "site"])
        if not val_def or force:
            fraw = Path(self.table.loc[irow, "fpath_inp"])
            site_found = arocnv.site_search_from_list(fraw, metadata_or_sites_list_inp)
            self.table.loc[irow, "site"] = site_found
        else:
            site_found = "XXXX00XXX"

        return site_found
