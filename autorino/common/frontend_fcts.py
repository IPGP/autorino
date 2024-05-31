#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 23/04/2024 14:21:56

@author: psakic
"""

import autorino.convert as arocnv
import autorino.handle as arohdl
import os



def convert_rnx(raws_inp, out_dir, tmp_dir=None, log_dir=None,
                out_dir_structure='<SITE_ID4>/%Y/',
                rinexmod_options=None,
                metadata=None,
                force=False):
    """
    Frontend function that performs RAW > RINEX conversion.

    Parameters
    ----------
    raws_inp : list
        The input RAW files to be converted.
    out_dir : str
        The output directory where the converted files will be stored.
    tmp_dir : str, optional
        The temporary directory used during the conversion process.
        If not provided, it defaults to <out_dir>/tmp_convert_rnx.
        Defaults to None.
    log_dir : str, optional
        The directory where logs will be stored. If not provided, it defaults to tmp_dir.
         Defaults to None.
    out_dir_structure : str, optional
        The structure of the output directory.
        If provided, the converted files will be stored in a subdirectory of out_dir following this structure.
        See README.md for more information. Typical values are '<SITE_ID4>/%Y/' or '%Y/%j/'.
        Default value is '<SITE_ID4>/%Y/'.
    rinexmod_options : dict, optional
        The options for modifying the RINEX files during the conversion. Defaults to None.
    metadata : str or list, optional
        The metadata to be included in the converted RINEX files. Possible inputs are:
         * list of string (sitelog file paths),
         * single string (single sitelog file path)
         * single string (directory containing the sitelogs)
         * list of MetaData objects
         * single MetaData object. Defaults to None.
    force : bool, optional
        If set to True, the conversion will be forced even if the output files already exist.
        Defaults to False.

    Returns
    -------
    None
    """
    if not tmp_dir:
        tmp_dir = os.path.join(out_dir, 'tmp_convert_rnx')

    if not log_dir:
        log_dir = tmp_dir

    if out_dir_structure:
        out_dir_use = os.path.join(out_dir, out_dir_structure)
    else:
        out_dir_use = out_dir

    cnv = arocnv.ConvertGnss(out_dir_use, tmp_dir, log_dir, metadata=metadata)
    cnv.load_table_from_filelist(raws_inp)
    cnv.convert(force=force, rinexmod_options=rinexmod_options)

    return None


def split_rnx(rnxs_inp, epo_inp, out_dir, tmp_dir, log_dir=None,
              handle_software='converto',
              rinexmod_options=None,
              metadata=None):
    """
    Frontend function to split RINEX files based on certain criteria

    Parameters
    ----------
    rnxs_inp : list
        The input RINEX files to be split
    epo_inp : str
        The input epoch for splitting the RINEX files
    out_dir : str
        The output directory where the split files will be stored
    tmp_dir : str
        The temporary directory used during the splitting process
    log_dir : str, optional
        The directory where logs will be stored. If not provided, it defaults to tmp_dir
    handle_software : str, optional
        The software to be used for handling the RINEX files during the split operation
    rinexmod_options : dict, optional
        The options for modifying the RINEX files during the split operation
    metadata : str or list, optional
        The metadata to be included in the split RINEX files
        Possible inputs are:
         * list of string (sitelog file paths),
         * single string (single sitelog file path)
         * single string (directory containing the sitelogs)
         * list of MetaData objects
         * single MetaData object

    Returns
    -------
    None
    """
    if not log_dir:
        log_dir = tmp_dir

    spt_store = arohdl.HandleGnss(out_dir, tmp_dir, log_dir, metadata=metadata)
    spt_store.load_table_from_filelist(rnxs_inp)
    spt_store.update_epoch_table_from_rnx_fname(use_rnx_filename_only=True)

    spt_split = arohdl.HandleGnss(out_dir, tmp_dir, log_dir, epo_inp, metadata=metadata)
    spt_split.find_rnxs_for_handle(spt_store)
    spt_split.split(handle_software=handle_software, rinexmod_options=rinexmod_options)

    return None


def splice_rnx(rnxs_inp,
               out_dir, tmp_dir, log_dir=None,
               handle_software='converto',
               period='1d',
               rolling_period=False,
               rolling_ref=-1,
               round_method='floor',
               drop_epoch_rnd=False,
               rinexmod_options=None,
               metadata=None):
    """
    Frontend function to splice RINEX files together based on certain criteria

    Parameters
    ----------
    rnxs_inp : list
        The input RINEX files to be spliced
    out_dir : str
        The output directory where the spliced files will be stored
    tmp_dir : str
        The temporary directory used during the splicing process
    log_dir : str, optional
        The directory where logs will be stored. If not provided, it defaults to tmp_dir
    handle_software : str, optional
        The software to be used for handling the RINEX files during the splice operation
    period : str, optional
        The period for splicing the RINEX files
    rolling_period : bool, optional
        Whether to use a rolling period for splicing the RINEX files
    rolling_ref : int, optional
        The reference for the rolling period
    round_method : str, optional
        The method for rounding the epochs during the splice operation
    drop_epoch_rnd : bool, optional
        Whether to drop the rounded epochs during the splice operation
    rinexmod_options : dict, optional
        The options for modifying the RINEX files during the splice operation
    metadata : str or list, optional
        The metadata to be included in the spliced RINEX files
        Possible inputs are:
         * list of string (sitelog file paths),
         * single string (single sitelog file path)
         * single string (directory containing the sitelogs)
         * list of MetaData objects
         * single MetaData object
    Returns
    -------
    spc_main_obj : object
        The main SpliceGnss object after the splice operation
    """
    if not log_dir:
        log_dir = tmp_dir

    spc_inp = arohdl.HandleGnss(out_dir, tmp_dir, log_dir, metadata=metadata)
    spc_inp.load_table_from_filelist(rnxs_inp)
    spc_inp.update_epoch_table_from_rnx_fname(use_rnx_filename_only=True)

    spc_main_obj, spc_objs_lis = spc_inp.divide_by_epochs(period=period,
                                                          rolling_period=rolling_period,
                                                          rolling_ref=rolling_ref,
                                                          round_method=round_method,
                                                          drop_epoch_rnd=drop_epoch_rnd)

    spc_main_obj.splice(handle_software=handle_software, rinexmod_options=rinexmod_options)

    return spc_main_obj
