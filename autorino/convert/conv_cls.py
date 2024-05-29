#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  7 12:07:18 2023

@author: psakic
"""

#### Import the logger
import logging
from pathlib import Path

import numpy as np

import autorino.common as arocmn
import autorino.convert as arocnv
from geodezyx import operational

logger = logging.getLogger(__name__)
logger.setLevel("INFO")


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
    metadata : str, optional
        The metadata associated with the conversion process.

    Methods
    -------
    __init__(self, out_dir, tmp_dir, log_dir, epoch_range=None, site=None, session=None, options=None, metadata=None)
        Initializes the ConvertGnss class with the specified parameters.
    """

    def __init__(self, out_dir, tmp_dir, log_dir,
                 epoch_range=None,
                 site=None,
                 session=None,
                 options=None,
                 metadata=None):
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
        metadata : str, optional
            The metadata associated with the conversion process.
        """
        super().__init__(out_dir, tmp_dir, log_dir,
                         epoch_range=epoch_range,
                         site=site,
                         session=session,
                         options=options,
                         metadata=metadata)

    ###############################################

def convert(self, print_table=False, force=False, rinexmod_options=None):
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
    print_table : bool, optional
        If True, prints the conversion table. Default is False.
    force : bool, optional
        If True, forces the conversion even if output files already exist. Default is False.
    rinexmod_options : dict, optional
        A dictionary containing options for the rinexmod process. If not specified, default options are used.

    Returns
    -------
    None
    """

        ### here the None to dict is necessary, because we use a defaut rinexmod_options bellow
        if rinexmod_options is None:
            rinexmod_options = {}

        logger.info("******** RAW > RINEX files conversion")

        self.set_tmp_dirs_paths()
        ### other tmps subdirs come also later in the loop

        if self.metadata:
            site4_list = arocnv.site_list_from_metadata(self.metadata)
        else:
            site4_list = []

        ### initialize the table as log
        self.set_table_log(out_dir=self.tmp_dir_logs)

        ### guess and deactivate existing local RINEX files
        if not force:
            self.guess_local_rnx_files()
            self.check_local_files()
            self.filter_ok_out()

        self.tmp_decmp_files , _ = self.decompress()

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

            #_ = self.set_tmp_dirs_paths()

            ### since the site code from fraw can be poorly formatted
            # we search it w.r.t. the sites from the metadata
            site = arocnv.site_search_from_list(fraw,
                                                site4_list)

            ##### something better must be done with
            # rinexmod.rinexmod_api.metadata_find_site() !!!!
            # clarify the site4 and the site9 usage
            # create method update_site_table_from_fname

            ### we update the table row and the translate dic (necessary for the output dir)
            self.table.loc[irow, 'site'] = site
            self.site_id = site
            self.set_translate_dict()

            ### do a first converter selection by removing odd files 
            converter_name_use = arocnv.select_conv_odd_file(fraw)

            logger.info("extension/converter: %s/%s", ext, converter_name_use)

            if not converter_name_use:
                logger.info("file skipped, no converter found: %s", fraw)
                self.table.loc[irow, 'note'] = "no converter found"
                self.table.loc[irow, 'ok_inp'] = False
                self.write_in_table_log(self.table.loc[irow])

            ### a function to stop the docker containers running for too long
            # (for trimble conversion)
            arocnv.stop_long_running_containers()

            #############################################################
            ###### CONVERSION
            frnxtmp = self.on_row_convert(irow, self.tmp_dir_converted,
                                          converter_inp=converter_name_use)
            self.tmp_rnx_files.append(frnxtmp)  ### list for final remove

            #############################################################
            ###### RINEXMOD
            rinexmod_options_use = rinexmod_options.copy()
            rinexmod_options_use.update({'marker':site,
                                         'sitelog':self.metadata})

            self.on_row_rinexmod(irow, self.tmp_dir_rinexmoded,
                                 rinexmod_options=rinexmod_options_use)

            #############################################################
            ###### FINAL MOVE
            self.on_row_move_final(irow)

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

    def on_row_convert(self, irow, out_dir = None, converter_inp='auto', table_col = 'fpath_inp'):
        """
        "on row" method

        Converts the 'table_col' entry for each row of the table.

        This method is applied to each row of the table. It converts the 'table_col' entry, typically a file.
        The conversion is performed using the specified converter. If no converter is specified, an automatic converter is used.
        The output of the conversion is stored in the specified output directory. If no output directory is specified, the output is stored in the temporary directory.

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

        if not self.table.loc[irow, 'ok_inp']:
            logger.warning("action on row skipped (input disabled): %s",
                           self.table.loc[irow, 'fname'])
            return None

        # definition of the output directory (after the action)
        if out_dir:
            out_dir_use = out_dir
        elif hasattr(self, 'tmp_dir_converted'):
            out_dir_use = self.tmp_dir_converted
        else:
            out_dir_use = self.tmp_dir

        try:
            frnxtmp, _ = arocnv.converter_run(self.table.loc[irow, table_col],
                                              out_dir,
                                              converter=converter_inp)
        except Exception as e:
            logger.error("something went wrong for %s",
                         self.table.loc[irow, table_col])
            logger.error("Exception raised: %s",e)
            frnxtmp = None

        if frnxtmp:
            ### update table if things go well
            self.table.loc[irow, 'ok_out'] = True
            self.table.loc[irow, 'fpath_out'] = frnxtmp
            epo_srt_ok, epo_end_ok = operational.rinex_start_end(frnxtmp)
            self.table.loc[irow, 'epoch_srt'] = epo_srt_ok
            self.table.loc[irow, 'epoch_end'] = epo_end_ok
        else:
            ### update table if things go wrong
            self.table.loc[irow, 'ok_out'] = False
        return frnxtmp