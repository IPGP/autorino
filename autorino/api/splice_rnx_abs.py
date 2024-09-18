#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 18/09/2024 18:26:05

@author: psakic
"""

import glob
import os

import autorino.cfgfiles as arocfg
import autorino.download as arodwl
import autorino.convert as arocnv
import autorino.handle as arohdl
import autorino.common as arocmn

#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger(__name__)
logger.setLevel(aroenv.aro_env_dict["general"]["log_level"])


def splice_rnx_abs(
    rnxs_inp,
    epoch_srt,
    epoch_end,
    period,
    out_dir,
    tmp_dir,
    log_dir=None,
    handle_software="converto",
    rinexmod_options=None,
    metadata=None,
):
    """
    Splice RINEX files together in an absolute way, based on the provided epoch range.

    This function takes in a list of RINEX files and splices them together based on the specified
    epoch range and other criteria. The spliced files are stored in the specified output directory.

    Parameters
    ----------
    rnxs_inp : list
        The input RINEX files to be spliced.
    epoch_srt : str
        The start epoch for the splicing operation.
    epoch_end : str
        The end epoch for the splicing operation.
    period : str
        The period for the splicing operation.
    out_dir : str
        The output directory where the spliced files will be stored.
    tmp_dir : str
        The temporary directory used during the splicing process.
    log_dir : str, optional
        The directory where logs will be stored. If not provided, it defaults to tmp_dir.
    handle_software : str, optional
        The software to be used for handling the RINEX files during the splice operation. Defaults to "converto".
    rinexmod_options : dict, optional
        The options for modifying the RINEX files during the splice operation. Defaults to None.
    metadata : str or list, optional
        The metadata to be included in the spliced RINEX files. Possible inputs are:
         * list of string (sitelog file paths),
         * single string (single sitelog file path),
         * single string (directory containing the sitelogs),
         * list of MetaData objects,
         * single MetaData object. Defaults to None.

    Returns
    -------
    object
        The SpliceGnss object after the splice operation.
    """
    if not log_dir:
        log_dir = tmp_dir

    epo_rng = arocmn.EpochRange(epoch_srt, epoch_end, period)

    spc = arohdl.SpliceGnss(
        out_dir, tmp_dir, log_dir, epoch_range=epo_rng, metadata=metadata
    )

    spc.splice(
        input_mode="given",
        input_rinexs=rnxs_inp,
        handle_software=handle_software,
        rinexmod_options=rinexmod_options,
    )

    return spc
