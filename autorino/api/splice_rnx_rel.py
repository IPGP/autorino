#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 18/09/2024 18:26:37

@author: psakic
"""



import autorino.handle as arohdl


#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger('autorino')
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])



def splice_rnx_rel(
    rnxs_inp,
    out_dir,
    tmp_dir,
    log_dir=None,
    handle_software="converto",
    period="1d",
    rolling_period=False,
    rolling_ref=-1,
    round_method="floor",
    drop_epoch_rnd=False,
    rinexmod_options=None,
    metadata=None,
):
    """
    Splices RINEX files together in a relative way, based on certain criteria.

    This function takes in a list of RINEX files and splices them together based on the provided criteria.
    The spliced files are stored in the specified output directory.

    Parameters
    ----------
    rnxs_inp : list
        The input RINEX files to be spliced.
        The input can be:
        * a python list
        * a text file path containing a list of files
        * a tuple containing several text files path
        * a directory path.
    out_dir : str
        The output directory where the spliced files will be stored.
    tmp_dir : str
        The temporary directory used during the splicing process.
    log_dir : str, optional
        The directory where logs will be stored. If not provided, it defaults to tmp_dir.
    handle_software : str, optional
        The software to be used for handling the RINEX files during the splice operation.
        Defaults to "converto".
    period : str, optional
        The period for splicing the RINEX files. Defaults to "1d".
    rolling_period : bool, optional
        Whether to use a rolling period for splicing the RINEX files.
        If False, the spliced files will be based only on the "full" period provided,
        i.e. Day1 00h-24h, Day2 00h-24h, etc.
        If True, the spliced files will be based on the rolling period.
        i.e. Day1 00h-Day2 00h, Day1 01h-Day2 01h, Day1 02h-Day2 02h etc.
        Defaults to False.
        see also eporng_fcts.round_epochs function
    rolling_ref :  datetime-like or int, optional
        The reference for the rolling period.
        If datetime-like object, use this epoch as reference.
        If integer, use the epoch of the corresponding index
        Use -1 for the last epoch for instance.
        The default is -1.
        see also eporng_fcts.round_epochs function
    round_method : str, optional
        The method for rounding the epochs during the splice operation. Defaults to "floor".
    drop_epoch_rnd : bool, optional
        Whether to drop the rounded epochs during the splice operation. Defaults to False.
    rinexmod_options : dict, optional
        The options for modifying the RINEX files during the splice operation. Defaults to None.
    metadata : str or list, optional
        The metadata to be included in the spliced RINEX files. Possible inputs are:
         * list of string (sitelog file paths),
         * single string (single sitelog file path)
         * single string (directory containing the sitelogs)
         * list of MetaData objects
         * single MetaData object. Defaults to None.

    Returns
    -------
    spc_main_obj : object
        The main SpliceGnss object after the splice operation.
    """
    if not log_dir:
        log_dir = tmp_dir

    spc_inp = arohdl.SpliceGnss(out_dir, tmp_dir, log_dir, metadata=metadata)
    spc_inp.load_tab_filelist(rnxs_inp)
    spc_inp.updt_epotab_rnx(use_rnx_filename_only=True)

    spc_main_obj, spc_objs_lis = spc_inp.group_by_epochs(
        period=period,
        rolling_period=rolling_period,
        rolling_ref=rolling_ref,
        round_method=round_method,
        drop_epoch_rnd=drop_epoch_rnd,
    )

    spc_main_obj.splice_core(
        handle_software=handle_software, rinexmod_options=rinexmod_options
    )

    return spc_main_obj
