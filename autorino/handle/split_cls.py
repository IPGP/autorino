#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 20/05/2025 20:26:44

@author: psakic
"""
from __future__ import annotations

# Create a logger object.
import autorino.common as arocmn
import autorino.convert as arocnv
import autorino.handle.handle_cls as arohdlcls

# +++ Import the logger
import logging
import autorino.cfgenv.env_read as aroenv
from typing import Any

logger = logging.getLogger("autorino")
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])

BOLD_SRT = "\033[1m"
BOLD_END = "\033[0m"

#   _____       _ _ _
#  / ____|     | (_) |
# | (___  _ __ | |_| |_
#  \___ \| '_ \| | | __|
#  ____) | |_) | | | |_
# |_____/| .__/|_|_|\__|
#        | |
#        |_|


class SplitGnss(arohdlcls.HandleGnss):
    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize a SplitGnss object.

        This constructor initializes a SplitGnss object, which is used for handling
        the splitting of RINEX files. It inherits from the HandleGnss class.

        Parameters
        ----------
        **kwargs : keyword arguments
            Additional keyword arguments passed to the parent HandleGnss class.
            Common parameters include:
            - out_dir : str - The output directory for the split RINEX files.
            - tmp_dir : str - The temporary directory for intermediate files.
            - log_dir : str - The directory for log files.
            - inp_dir : str, optional - The input directory for raw files. Default is None.
            - inp_file_regex : str, optional - Regular expression pattern for input files.
            - epoch_range : EpochRange, optional - The range of epochs to be processed. Default is None.
            - site : dict, optional - Information about the site. Default is None.
            - session : dict, optional - Information about the session. Default is None.
            - options : dict, optional - Additional options for the splitting operation. Default is None.
            - metadata : str or list, optional - Metadata for the splitting operation. Default is None.
        """
        super().__init__(**kwargs)

    def split(
        self,
        input_mode: str = "given",
        input_rinexs: str | list | Any | None = None,
        handle_software: str = "converto",
        handle_software_options: str | list[str] | None = None,
        rinexmod_options: dict | None = None,
        verbose: bool = False,
        force: bool = False,
        reverse_order: bool = False,
        add_extra_margin: bool = False
    ) -> None:
        """
        Split RINEX files.

        This method splits RINEX files based on the provided input. It can find local input files,
        convert a list of RINEX files to a StepGnss object, or use an existing StepGnss object.
        The splitting operation is performed using the specified software and options.

        Parameters
        ----------
        input_mode : str, optional
            The mode for finding input RINEX files. It can be:
            - "find": to find local input files.
            - "given": to use provided input RINEX files.
            Default is "given".
        input_rinexs : str or list or StepGnss or None, optional
            The input RINEX files. It can be:
            - A list of RINEX file paths.
            - An existing StepGnss object.
            Default is None.
        handle_software : str, optional
            The software to use for handling the RINEX files. Default is "converto".
        handle_software_options : str or list of str or None, optional
            Additional options for the handling software. It can be:
            - A string of options to be passed to the software.
            - A list of strings, where each string is an option to be passed to the software.
            - None, if no additional options are needed. Default is None.
        rinexmod_options : dict, optional
            Additional options for the RINEX modification. Default is None.
        verbose : bool, optional
            If True, prints the table for debugging purposes. Default is False.
        force : bool, optional
            If True, forces the splitting operation. Default is False.
        reverse_order : bool, optional
            If True, processes the files in reverse order (anti-chronological, newer first).
            Default is False.
        add_extra_margin : bool, optional
            If True, adds an extra margin to the epochs for splitting. Default is False.

        Returns
        -------
        None
        """
        # set the log file
        self.set_logfile()

        # Log the start of the splitting operation
        logger.info(BOLD_SRT + ">>>>>> Splitting RINEX files" + BOLD_END)

        # set the ok_inp to True per default
        self.table["ok_inp"] = True

        # generate the potential local files
        self.guess_local_rnx()
        # tests if the output local files are already there
        self.check_loc_files("out")
        # switch ok_inp to False if the output files are already there
        self.filter_ok_out()
        # if force is True, force the splicing operation
        if force:
            self.force("split")
        if reverse_order:
            self.reverse_table()

        # Find the input RINEX files
        stp_obj_rnxs_inp = self.load_input_rnxs(str(input_mode), input_rinexs)

        # Feed the epochs for splitting
        self.feed_by_epochs(stp_obj_rnxs_inp, mode="split", print_table=verbose, add_extra_margin=add_extra_margin)

        # Perform the core splitting operation
        self.split_core(
            handle_software=handle_software,
            handle_software_options=handle_software_options,
            rinexmod_options=rinexmod_options
        )

        # close the log file
        self.close_logfile()

        return None

    def split_core(
        self,
        handle_software: str = "converto",
        handle_software_options: str | list[str] | None = None,
        rinexmod_options: dict | None = None,
    ) -> None:
        """
        Perform the core splitting operation.

        This method handles the core splitting operation for RINEX files. It iterates over each row
        in the table, performs the splitting operation using the specified software, and applies
        RINEX modifications if necessary. Temporary files are removed after the operation.

        Parameters
        ----------
        handle_software : str, optional
            The software to use for handling the RINEX files. Default is "converto".
        handle_software_options : str or list of str or None, optional
            Additional options for the handling software. It can be:
            - A string of options to be passed to the software.
            - A list of strings, where each string is an option to be passed to the software.
            - None, if no additional options are needed. Default is None.
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
                "split",
                fname_custom=arocmn.iso_zulu_epoch(self.table.loc[irow, "epoch_srt"]),
            ):
                continue

            fdecmptmp, _ = self.mono_decompress(irow)
            self.tmp_decmp_files.append(fdecmptmp)

            frnx_splited = self.mono_split(
                irow,
                self.tmp_dir_converted,
                handle_software=handle_software,
                handle_software_options=handle_software_options,
            )
            if not self.table.loc[irow, "ok_out"]:
                logger.error("unable to split %s, skip", self.table.loc[irow])
                continue

            self.tmp_rnx_files.append(frnx_splited)

            self.mono_rinexmod(
                irow, self.tmp_dir_rinexmoded, rinexmod_options=rinexmod_options
            )

            if self.tmp_dir_rinexmoded != self.out_dir:
                self.mono_mv_final(irow, self.out_dir)

        self.remov_tmp_files()

        return None

    def mono_split(
        self,
        irow: Any,
        out_dir: str | None = None,
        table_col: str = "fpath_inp",
        handle_software: str = "converto",
        handle_software_options: str | list[str] | None = None,
    ) -> str | None:
        """
        "on row" method

        for each row of the table, split the 'table_col' entry,
        typically 'fpath_inp' file
        """

        if not self.mono_ok_check(
            irow,
            "split (mono)",
            fname_custom=arocmn.iso_zulu_epoch(self.table.loc[irow, "epoch_srt"]),
            switch_ok_out_false=True,
        ):
            return None

        # definition of the output directory
        if out_dir:
            out_dir_main_use = out_dir
        elif hasattr(self, "tmp_dir_converted"):
            out_dir_main_use = self.tmp_dir_converted
        else:
            out_dir_main_use = self.tmp_dir

        out_dir_use = self.translate_path(
            out_dir_main_use, self.table.loc[irow, "epoch_srt"]
        )

        frnx_inp = self.table.loc[irow, table_col]

        handl_opts, handl_kwopts = self.handl_soft_opts(
            irow,
            handl_soft=handle_software,
            mode="split",
            handl_opts_supl=handle_software_options,
        )
        try:
            frnxtmp, _ = arocnv.converter_run(
                frnx_inp,
                out_dir_use,
                converter=handle_software,
                bin_options=handl_opts,
                bin_kwoptions=handl_kwopts,
            )
        except Exception as e:
            logger.error("Error for %s", frnx_inp)
            logger.error("Exception raised: %s", e)
            frnxtmp = None

        if frnxtmp:
            self.table.loc[irow, "ok_out"] = True
            self.table.loc[irow, "fpath_out"] = frnxtmp
        else:
            self.table.loc[irow, "ok_out"] = False
            # raise e

        return frnxtmp
