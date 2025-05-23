#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 18/09/2024 18:25:28

@author: psakic
"""

import autorino.handle as arohdl
import autorino.common as arocmn

#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger('autorino')
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])


def split_rnx(
    rnxs_inp,
    epoch_srt,
    epoch_end,
    period,
    out_dir,
    tmp_dir,
    log_dir=None,
    site=None,
    data_frequency="30S",
    handle_software="converto",
    rinexmod_options=None,
    metadata=None,
):
    """
    Frontend function to split RINEX files based on certain criteria

    Parameters
    ----------
    rnxs_inp : list
        The input RINEX files to be split
        The input can be:
        * a python list
        * a text file path containing a list of files
        * a tuple containing several text files path
        * a directory path.
    epoch_srt : datetime-like
        The start epoch for the splicing operation.
    epoch_end : datetime-like
        The end epoch for the splicing operation.
    period : str
        The period for the splicing operation.
    out_dir : str
        The output directory where the split files will be stored
    tmp_dir : str
        The temporary directory used during the splitting process
    log_dir : str, optional
        The directory where logs will be stored. If not provided, it defaults to tmp_dir
    site : str, optional
        The site name to be used for the split RINEX files
        Facultative but highly recommended to detect exisiting files to be skipped.
        data_frequency : str, optional
        The data frequency for the spliced RINEX files.
        Facultative but highly recommended to detect exisiting files to be skipped.
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

    epo_rng = arocmn.EpochRange(epoch_srt, epoch_end, period)

    spt = arohdl.SplitGnss(out_dir, tmp_dir, log_dir,
                           epoch_range=epo_rng,
                           site={'site_id':site},
                           session={"data_frequency": data_frequency},
                           metadata=metadata)

    spt.split(
        input_mode="given",
        input_rinexs=rnxs_inp,
        handle_software=handle_software,
        rinexmod_options=rinexmod_options,
        verbose=True
    )

    return spt

