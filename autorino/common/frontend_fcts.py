#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 23/04/2024 14:21:56

@author: psakic
"""

import autorino.convert as arocnv
import autorino.handle as arohdl

def convert_rnx(raws_inp, out_dir, tmp_dir, log_dir=None,
                rinexmod_options=None,
                metadata=None):
    """
    Frontend function to perform RAW > RINEX conversion

    Parameters
    ----------
    raws_inp : list
        The input RAW files to be converted
    out_dir : str
        The output directory where the converted files will be stored
    tmp_dir : str
        The temporary directory used during the conversion process
    log_dir : str, optional
        The directory where logs will be stored. If not provided, it defaults to tmp_dir
    rinexmod_options : dict, optional
        The options for modifying the RINEX files during the conversion
    metadata : dict, optional
        The metadata to be included in the converted RINEX files

    Returns
    -------
    None
    """
    if not log_dir:
        log_dir = tmp_dir

    cnv = arocnv.ConvertGnss(out_dir, tmp_dir, log_dir, metadata=metadata)
    cnv.load_table_from_filelist(raws_inp)
    cnv.convert(force=True, rinexmod_options=rinexmod_options)

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
    metadata : dict, optional
        The metadata to be included in the split RINEX files

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
    metadata : dict, optional
        The metadata to be included in the spliced RINEX files

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