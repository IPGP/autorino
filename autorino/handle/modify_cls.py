#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 20/05/2025 20:27:15

@author: psakic
"""
from __future__ import annotations

import autorino.handle.handle_cls as arohdlcls

# +++ Import the logger
import logging
import autorino.cfgenv.env_read as aroenv
from typing import Any

logger = logging.getLogger("autorino")
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])

BOLD_SRT = "\033[1m"
BOLD_END = "\033[0m"

class ModifyGnss(arohdlcls.HandleGnss):
    def __init__(
        self,
        **kwargs: Any
    ) -> None:
        """
        Initialize a ModifyGnss object.

        This constructor initializes a ModifyGnss object,
        which is used for a stand-alone application of RinexMod
        actions on RINEX files.
        It inherits from the HandleGnss class.

        Parameters
        ----------
        **kwargs : keyword arguments
            Additional keyword arguments passed to the parent HandleGnss class.
            Common parameters include:
            - out_dir : str - The output directory for the modified RINEX files.
            - tmp_dir : str - The temporary directory for intermediate files.
            - log_dir : str - The directory for log files.
            - inp_dir : str, optional - The input directory for raw files. Default is None.
            - inp_file_regex : str, optional - Regular expression pattern for input files.
            - epoch_range : EpochRange, optional - The range of epochs to be processed. Default is None.
            - site : dict, optional - Information about the site. Default is None.
            - session : dict, optional - Information about the session. Default is None.
            - options : dict, optional - Additional options for the modification operation. Default is None.
            - metadata : str or list, optional - Metadata for the modification operation. Default is None.
        """
        super().__init__(**kwargs)

    def modify(
        self,
        verbose: bool = False,
        force: bool = False,
        reverse_order: bool = False,
        rinexmod_options: dict | None = None
    ) -> None:
        """
        Apply RINEX modifications to the data.

        This method iterates over the rows of the table and applies RINEX modifications
        using the specified options. It checks if the operation is valid for each row
        before proceeding.

        Parameters
        ----------
        verbose : bool, optional
            If True, prints the table of operations. Default is False.
        force : bool, optional
            If True, forces the rinexmod operation even if the output files already exist.
            Default is False.
        reverse_order : bool, optional
            If True, processes the files in reverse order (anti-chronological, newer first).
            Default is False.
        rinexmod_options : dict, optional
            The options to be used by the rinexmod function.
            If not provided, default options are used.

        Returns
        -------
        None
        """

        # set the log file
        self.set_logfile()

        # Log the start of the splitting operation
        logger.info(
            BOLD_SRT + ">>>>>> Modify RINEX files (stand-alone rinexmod)" + BOLD_END
        )

        # set the ok_inp to True per default
        self.table["ok_inp"] = True

        # dont know why I put this test/conditional block here
        # but I will keep it for now (202602)
        guess_local_rnx = True
        if guess_local_rnx:
            # special case if we downgrade the name
            if rinexmod_options and "shortname" in rinexmod_options.keys():
                shortname = rinexmod_options["shortname"]
            else:
                shortname = False

            # generate the potential local files
            self.guess_local_rnx(shortname=shortname)
            # tests if the output local files are already there
            self.check_loc_files("out")
            # switch ok_inp to False if the output files are already there
            self.filter_ok_out()

        # if force is True, force the splicing operation
        if force:
            self.force("modify")
        if reverse_order:
            self.reverse_table()

        # Find the input RINEX files
        # stp_obj_rnxs_inp = self.load_input_rnxs(input_mode, input_rinexs)

        if verbose:
            self.print_table()

        for irow, row in self.table.iterrows():
            # Check if the operation is valid for the current row
            if not self.mono_ok_check(irow, "modify"):
                continue

            # Update the RINEX modification options for the current row
            rinexmod_options_use = self.updt_rnxmodopts(
                rinexmod_options, irow, debug_print=False
            )

            out_dir_use = self.translate_path(
                self.out_dir, self.table.loc[irow, "epoch_srt"]
            )

            # Apply the RINEX modification using the updated options
            self.mono_rinexmod(
                irow,
                out_dir=out_dir_use,
                table_col="fpath_inp",
                rinexmod_options=rinexmod_options_use,
                check_ok_out=False
            )

        return None

