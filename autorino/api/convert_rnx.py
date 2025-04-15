#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 18/09/2024 18:24:43

@author: psakic
"""

import os
import autorino.convert as arocnv
import autorino.common as arocmn

#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger("autorino")
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])

def convert_rnx(
    inp_raws,
    out_dir,
    out_structure="<SITE_ID4>/%Y/",
    tmp_dir=None,
    log_dir=None,
    rinexmod_options=None,
    metadata=None,
    force=False,
    raw_out_dir=None,
    raw_out_structure=None,
):
    """
    Frontend function that performs RAW > RINEX conversion.

    Parameters
    ----------
    inp_raws : list
        The input RAW files to be converted.
        The input can be:
        * a python list
        * a text file path containing a list of files
        * a tuple containing several text files path
        * a directory path.
    out_dir : str
        The output directory where the converted files will be stored.
    out_structure : str, optional
        The structure of the output directory.
        If provided, the converted files will be stored in a subdirectory of out_dir following this structure.
        See README.md for more information.
        Typical values are '<SITE_ID4>/%Y/' or '%Y/%j/'.
        Default value is '<SITE_ID4>/%Y/'.
    tmp_dir : str, optional
        The temporary directory used during the conversion process.
        If not provided, it defaults to <out_dir>/tmp_convert_rnx.
        Defaults to None.
    log_dir : str, optional
        The directory where logs will be stored. If not provided, it defaults to tmp_dir.
         Defaults to None.
    rinexmod_options : dict, optional
        The options for modifying the RINEX files during the conversion. Defaults to None.
    metadata : str or list, optional
        The metadata to be included in the converted RINEX files. Possible inputs are:
         * list of string (sitelog file paths),
         * single string (single sitelog file path)
         * single string (directory containing the sitelogs)
         * list of MetaData objects
         * single MetaData object.
         Defaults to None.
    force : bool, optional
        If set to True, the conversion will be forced even if the output files already exist.
        Defaults to False.
    raw_out_dir : str, optional
        Directory where RAW files will be archived.
        No delete will occur, your RAW files are sacred.
        Defaults to None.
    raw_out_structure : str, optional
        Structure for archiving RAW files.
        Defaults to `out_structure` if not provided.


    Returns
    -------
    None
    """

    tmp_dir = tmp_dir or os.path.join(out_dir, "tmp_convert_rnx")
    log_dir = log_dir or tmp_dir
    out_dir_use = os.path.join(out_dir, out_structure) if out_structure else out_dir

    ###### Convert RAW > RINEX files
    raws_use = inp_raws
    cnv = arocnv.ConvertGnss(
        out_dir_use, tmp_dir, log_dir, metadata=metadata
    )
    cnv.load_tab_filelist(raws_use)
    cnv.convert(
        force=force,
        rinexmod_options=rinexmod_options,
    )

    ###### Archive the RAW files
    if raw_out_dir:
        logger.info(">>>>>> RAW files archive" )
        if not raw_out_structure:
            raw_out_structure = out_structure
        raw_out_dir_use = str(os.path.join(raw_out_dir, raw_out_structure))

        cpy_raw = arocmn.StepGnss(
            raw_out_dir_use, tmp_dir, log_dir, metadata=metadata
        )

        cpy_raw.load_tab_prev_tab(cnv.table)
        cpy_raw.table["fpath_inp"] = cnv.table["fpath_inp"]
        cpy_raw.table["fname"] = cpy_raw.table["fpath_inp"].apply(os.path.basename)
        #cpy_raw.print_table()
        cpy_raw.guess_out_files()
        #cpy_raw.print_table()
        cpy_raw.filter_ok_out()
        #cpy_raw.print_table()
        cpy_raw.move_files(mode="inpout", force=force, copy_only=True)
        #cpy_raw.print_table()

    return cnv
