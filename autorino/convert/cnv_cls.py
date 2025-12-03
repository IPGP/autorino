#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  7 12:07:18 2023

@author: psakic
"""

from pathlib import Path

import numpy as np
import pandas as pd

import autorino.common as arocmn
import autorino.convert as arocnv
from geodezyx import operational as gzyx_opera

#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger("autorino")
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])

BOLD_SRT = "\033[1m"
BOLD_END = "\033[0m"


class ConvertGnss(arocmn.StepGnss):
    """
    A class used to represent the GNSS conversion process.

    This class inherits from the StepGnss class
    and is used to handle the conversion of GNSS data.

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
    __init__(self, out_dir, tmp_dir, log_dir, epoch_range_inp=None, site=None, session=None, options=None, metadata=None)
        Initializes the ConvertGnss class with the specified parameters.
    """

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

    ###############################################

    def convert(
        self,
        verbose=False,
        force=False,
        rinexmod_options=None,
        converter="auto",
        filter_prev_tables=False,
        conv_regex_custom_main=None,
        conv_regex_custom_annex=None,
    ):
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
            A dictionary containing options for the rinexmod process.
             If not specified, default options are used.
        converter : str, optional
            The converter to be used for the conversion.
            If not specified, the best converter is automatically selected.
            Default is 'auto'.
        filter_prev_tables : bool, optional
            If True, filters and skip previously converted files
            with tables stored in the tmp tables directory.
            Default is False.
        conv_regex_custom_main : str, optional
            A custom regular expression to catch the main converted file.
            If not specified, no custom regex is used.
            Default is None.
        conv_regex_custom_annex : str, optional
            A custom regular expression to catch naming the annex converted file.
            If not specified, no custom regex is used.
            Default is None.

        Returns
        -------
        None
        """

        # #### Legacy Option
        # update_site_id_with_metadata : bool, optional
        #     If True, updates the site identifier using the metadata (default case).
        #     Since the site code from RAW file name can be poorly formatted
        #     we search it w.r.t. the sites from the metadata.
        #     If False, the site identifier is not updated, and it is the one of the
        #     ConvertGnss object self.site_id that is used.
        #     (for some advanced cases).
        #     Default is True.

        self.set_logfile()
        logger.info(BOLD_SRT + ">>>>>> RAW > RINEX files conversion" + BOLD_END)

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
        self.set_table_log(out_dir=self.tmp_dir_tables)

        ### guess and deactivate existing local RINEX files
        # generate the potential local files
        self.guess_local_rnx()
        # tests if the input local files are here
        self.check_local_files("inp")
        # tests if the output local files are already there
        self.check_local_files("out")
        # be sure ok_xxx columns are booleans
        self.table_ok_cols_bool()
        # switch ok_inp to False if the output files are already there
        self.filter_ok_out()

        if force:
            self.force("convert")

        if filter_prev_tables:
            logger.debug(f"Loading filter previous tables in: {self.tmp_dir_tables:}")
            prv_tbl_df = arocmn.load_previous_tables(self.tmp_dir_tables)
            # Filter previous tables stored in log_dir
            if len(prv_tbl_df) > 0:
                self.get_vals_prev_tab(prv_tbl_df)
                self.filter_prev_tab(prv_tbl_df)
            # switch ok_inp to False if the output files are already there
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
            n_tot_inp,
        )

        if verbose:
            self.print_table()

        ######################### START THE LOOP ##############################
        for irow, row in self.table.iterrows():
            fraw = Path(self.table.loc[irow, "fpath_inp"])
            ext = fraw.suffix.lower()

            if not self.mono_ok_check(irow, "conversion"):
                continue

            logger.info(">>>> input raw file for conversion: %s", fraw.name)

            ###########################################################################
            # change the site_id here is a very bad idea, it f*cks the outdir 240605
            # (the outdir has not the country code anymore)
            #
            # but, because of the new IGS update (9 char in sitlog)
            # it should not be a pb anymore

            # +++ since the site code from fraw can be poorly formatted
            # we search it w.r.t. the sites from the metadata
            # we update the table row and the translate_dic (necessary for the output dir)
            self.mono_site_upd(irow, site4_list)
            # set self.site_id for the output dir translation & rinexmod options
            self.site_id = self.table.loc[irow, "site"]

            self.set_translate_dict()
            ###########################################################################
            # +++ CONVERTER SELECTION

            if converter != "auto":
                converter_name_use = converter  # converter is forced
            else:
                # ++ do a first converter selection by identifying odd files
                converter_name_use = arocnv.slct_conv_odd_f(fraw)
                # NB: converter selection for regular files is done in
                # autorino.conv_cmd_run._convert_select

            logger.info("extension/converter: %s/%s", ext, converter_name_use)

            if not converter_name_use:
                logger.info("file skipped, no converter found: %s", fraw)
                self.table.loc[irow, "note"] = "no converter found"
                self.table.loc[irow, "ok_inp"] = False
                self.write_in_table_log(self.table.loc[irow])

            ## prepare the custom regex function if any
            # if not, conv_regex_fct_use is None and the default regexs
            # from autorino.convert.converter_run are set later
            conv_regex_fct_use = arocnv.prep_rgx_custom(conv_regex_custom_main, conv_regex_custom_annex)

            # ++ a function to stop the docker containers running for too long
            # (for trimble conversion)
            arocnv.stop_old_docker()

            #############################################################
            # +++++ CONVERSION
            frnxtmp = self.mono_convert(
                irow, self.tmp_dir_converted,
                converter_inp=converter_name_use,
                conv_regex_fct_inp=conv_regex_fct_use
            )
            self.tmp_rnx_files.append(frnxtmp)  # list for final remove

            #############################################################
            # +++++ RINEXMOD
            rinexmod_options_use = self.updt_rnxmodopts(
                rinexmod_options, irow, debug_print=False
            )

            self.mono_rinexmod(
                irow, self.tmp_dir_rinexmoded,
                rinexmod_options=rinexmod_options_use
            )
            #############################################################

            # +++++ FINAL MOVE
            self.mono_mv_final(irow, force=force)

        # ++++ remove temporary files
        self.remov_tmp_files()

        # close the log file
        self.close_logfile()

        return None

    #               _   _
    #     /\       | | (_)
    #    /  \   ___| |_ _  ___  _ __  ___    ___  _ __    _ __ _____      _____
    #   / /\ \ / __| __| |/ _ \| '_ \/ __|  / _ \| '_ \  | '__/ _ \ \ /\ / / __|
    #  / ____ \ (__| |_| | (_) | | | \__ \ | (_) | | | | | | | (_) \ V  V /\__ \
    # /_/    \_\___|\__|_|\___/|_| |_|___/  \___/|_| |_| |_|  \___/ \_/\_/ |___/
    #

    def mono_convert(
        self, irow, out_dir=None, converter_inp="auto", table_col="fpath_inp", conv_regex_fct_inp=None
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
            The directory where the output of the conversion should be stored.
             If not specified, the output is stored
            in the temporary directory.
        converter_inp : str, optional
            The converter to be used for the conversion.
             If not specified, an automatic converter is used.
        table_col : str, optional
            The column in the table that should be converted.
            Typically, this is a file. Default is 'fpath_inp'.
        conv_regex_fct_inp : function, optional
            A custom function returning regexs to catch
            the main and annex converted file names.

        Returns
        -------
        str
            The path of the converted file.
        """

        if not self.mono_ok_check(irow, "conversion"):
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
                self.table.loc[irow, table_col],
                out_dir_use,
                converter=converter_inp,
                conv_regex_fct= conv_regex_fct_inp
            )
        except Exception as e:
            logger.error("Error for: %s", self.table.loc[irow, table_col])
            logger.error("Exception raised: %s", e)
            frnxtmp = None

        if frnxtmp:
            ### update table if things go well
            self.table.loc[irow, "ok_out"] = True
            self.table.loc[irow, "fpath_out"] = frnxtmp
            epo_srt_ok, epo_end_ok = gzyx_opera.rinex_start_end(frnxtmp)
            self.table.loc[irow, "epoch_srt"] = pd.to_datetime(epo_srt_ok, utc=True)
            self.table.loc[irow, "epoch_end"] = pd.to_datetime(epo_end_ok, utc=True)
        else:
            ### update table if things go wrong
            self.table.loc[irow, "ok_out"] = False
        return frnxtmp

    def mono_site_upd(self, irow, metadata_or_sites_list_inp, force=False):
        """
        Updates the 'site' entry for each row of the table.

        This method is applied to each row of the table.
        It checks if the 'site' entry is defined.
        If it is not defined or if the 'force' parameter
        is set to True, it updates the 'site' entry.
        The update is performed by searching the site
        from a list of sites or metadata.
        If the 'site' entry is already defined and 'force' is not set to True,
        it sets the 'site' entry to 'XXXX00XXX'.

        Parameters
        ----------
        irow : int
            The index of the row in the table to be updated.
        metadata_or_sites_list_inp : list
            A list of sites or metadata from which the site should be searched.
        force : bool, optional
            If True, forces the update of the 'site'
            entry even if it is already defined.
            Default is False.

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
