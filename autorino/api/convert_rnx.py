#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 18/09/2024 18:24:43

@author: psakic
"""

import os
import autorino.convert as arocnv
import autorino.common as arocmn
import logging
import autorino.cfgenv.env_read as aroenv
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

import multiprocessing as mp
import geodezyx.utils

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
    force_rnx=False,
    force_raw=False,
    raw_out_dir=None,
    raw_out_structure=None,
    processes=1,
    filter_prev_tables=False
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
        The metadata to be included in the converted RINEX files.
        Possible inputs are:
         * list of string (sitelog file paths),
         * single string (single sitelog file path)
         * single string (directory containing the sitelogs)
         * list of MetaData objects
         * single MetaData object.
         Defaults to None.
    force_rnx : bool, optional
        If set to True, the conversion will be forced even if the output files already exist.
        Defaults to False.
    force_raw : bool, optional
        If set to True, the RAW file archiving will be forced even if the output files already exist.
        Defaults to False.
    raw_out_dir : str, optional
        Directory where RAW files will be archived.
        No delete will occur, your RAW files are sacred.
        Defaults to None.
    raw_out_structure : str, optional
        Structure for archiving RAW files.
        Defaults to `out_structure` if not provided.
    processes : int, optional
        Number of processes to use for parallel conversion. Default is 1.
    filter_prev_tables : bool, optional
        If True, filters and skip previously converted files
        with tables stored in the tmp tables directory.
        Default is False.

    Returns
    -------
    None
    """
    tmp_dir = tmp_dir or os.path.join(out_dir, "tmp_convert_rnx")
    log_dir = log_dir or tmp_dir
    out_dir_use = os.path.join(out_dir, out_structure) if out_structure else out_dir

    ###### Convert RAW > RINEX files
    inp_raws_chunked = geodezyx.utils.chunkIt(inp_raws, processes)

    args_wrap = []
    for raws in inp_raws_chunked:
        args = (
            raws,
            out_dir_use,
            tmp_dir,
            log_dir,
            metadata,
            force_rnx,
            rinexmod_options,
            filter_prev_tables
        )
        args_wrap.append(args)

    # Parallel RAW > RINEX conversion

    #### ++++ new style concurrent.futures
    cnv_out_lis = []
    # pool_exec = ThreadPoolExecutor
    pool_exec = ProcessPoolExecutor
    with pool_exec(max_workers=processes) as executor:
        futures = [executor.submit(convert_raw_wrap, args) for args in args_wrap]
        for f in as_completed(futures):
            cnv_out_lis.append(f.result())

    #### ++++ classic multiprocessing
    # pool = mp.Pool(processes=processes)
    # try:
    #     _ = pool.map(convert_raw_wrap, args_wrap, chunksize=1)
    # except Exception as e:
    #     logger.error("error in the pool.map : %s", e)
    #
    # pool.close()

    ###### Archive the RAW files
    if raw_out_dir:
        logger.info(">>>>>> RAW files archive")
        if not raw_out_structure:
            raw_out_structure = out_structure
        raw_out_dir_use = str(os.path.join(raw_out_dir, raw_out_structure))

        for cnv in cnv_out_lis:
            cpy_raw = arocmn.StepGnss(raw_out_dir_use, tmp_dir, log_dir, metadata=metadata)
            debug_print = False

            # the table from the ConvertGnss object
            # is necessary to get the epoch
            cpy_raw.load_tab_prev_tab(cnv.table)
            cpy_raw.table["fpath_inp"] = cnv.table["fpath_inp"]
            cpy_raw.table["fname"] = cpy_raw.table["fpath_inp"].apply(os.path.basename)
            cpy_raw.print_table() if debug_print else None
            cpy_raw.guess_out_files()
            cpy_raw.print_table() if debug_print else None
            cpy_raw.filter_ok_out()
            cpy_raw.print_table() if debug_print else None
            cpy_raw.move_files(mode="inpout", force=force_raw, copy_only=True)
            cpy_raw.print_table() if debug_print else None

    return cnv_out_lis


def convert_raw_wrap(args):
    """
    Wrapper function for converting RAW GNSS files to RINEX format.

    Parameters
    ----------
    args : tuple
        A tuple containing the following arguments:
        - raws : list
            List of RAW files to be converted.
        - out_dir_use : str
            The output directory where the converted files will be stored.
        - tmp_dir : str
            Temporary directory used during the conversion process.
        - log_dir : str
            Directory where logs will be stored.
        - metadata : str or list
            Metadata to be included in the converted RINEX files.
        - force_rnx : bool
            If True, forces the conversion even if output files already exist.
        - rinexmod_options : dict
            Options for modifying the RINEX files during the conversion.
        - filter_prev_tables : bool
            If True, filters and skips previously converted files with
            tables stored in the tmp tables directory.

    Returns
    -------
    arocnv.ConvertGnss
        An instance of the `ConvertGnss` class containing the results of the conversion.
    """
    raws, out_dir_use, tmp_dir, log_dir, metadata, force_rnx, rinexmod_options, filter_prev_tables = args
    # Initialize the ConvertGnss object with the provided directories and metadata
    cnv = arocnv.ConvertGnss(out_dir_use, tmp_dir, log_dir, metadata=metadata)
    # Load the list of RAW files to be converted
    cnv.load_tab_filelist(raws)
    # Perform the conversion with the specified options
    cnv.convert(force=force_rnx, rinexmod_options=rinexmod_options,
                filter_prev_tables=filter_prev_tables)
    # Return the ConvertGnss object containing the conversion results
    return cnv

