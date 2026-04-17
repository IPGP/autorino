#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 18/09/2024 18:26:05

@author: psakic
"""

import autorino.handle as arohdl
import autorino.common as arocmn
import datetime as dt

#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger('autorino')
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])


def splice_rnx(
    rnxs_inp,
    out_dir,
    tmp_dir,
    period="1d",
    log_dir=None,
    epoch_srt=None,
    epoch_end=None,
    site=None,
    data_frequency="30S",
    handle_software="converto",
    rolling_period=False,
    rolling_ref=-1,
    round_method="floor",
    drop_epoch_rnd=False,
    rinexmod_options=None,
    metadata=None,
):
    """
    Splice RINEX files together, either in an absolute way (based on a
    provided epoch range) or in a relative way (based on the epochs found
    in the input files themselves).

    If ``epoch_srt`` and ``epoch_end`` are provided, the function operates
    in **absolute** mode: it builds an explicit epoch range and splices the
    input RINEX files accordingly.

    If ``epoch_srt`` and ``epoch_end`` are *not* provided, the function
    operates in **relative** mode: it groups the input files by their own
    epochs and splices each group.

    Parameters
    ----------
    rnxs_inp : list
        The input RINEX files to be spliced.
        The input can be:
        * a python list,
        * a text file path containing a list of files,
        * a tuple containing several text files path,
        * a directory path.
    out_dir : str
        The output directory where the spliced files will be stored.
    tmp_dir : str
        The temporary directory used during the splicing process.
    period : str, optional
        The period for splicing the RINEX files. Defaults to ``"1d"``.
    log_dir : str, optional
        The directory where logs will be stored. Defaults to ``tmp_dir``.
    epoch_srt : str or datetime-like, optional
        The start epoch for the splicing operation (*absolute* mode only).
        If ``None``, *relative* mode is used. Defaults to ``None``.
    epoch_end : str or datetime-like, optional
        The end epoch for the splicing operation (*absolute* mode only).
        If ``None``, *relative* mode is used. Defaults to ``None``.
    site : str, optional
        The site name to be used for the spliced RINEX files (*absolute* mode).
        Facultative but highly recommended to detect existing files to be
        skipped. Defaults to ``None``.
    data_frequency : str, optional
        The data frequency for the spliced RINEX files (*absolute* mode).
        Facultative but highly recommended to detect existing files to be
        skipped. Defaults to ``"30S"``.
    handle_software : str, optional
        The software to be used for handling the RINEX files during the
        splice operation. Defaults to ``"converto"``.
    rolling_period : bool, optional
        (*Relative* mode only.)
        Whether to use a rolling period for splicing the RINEX files.
        If ``False``, the spliced files will be based only on the "full"
        period provided, i.e. Day1 00h-24h, Day2 00h-24h, etc.
        If ``True``, the spliced files will be based on the rolling period,
        i.e. Day1 00h-Day2 00h, Day1 01h-Day2 01h, etc.
        Defaults to ``False``.
    rolling_ref : datetime-like or int, optional
        (*Relative* mode only.)
        The reference for the rolling period.
        If a datetime-like object, that epoch is used as reference.
        If an integer, the epoch at that index is used (e.g. ``-1`` for the
        last epoch). Defaults to ``-1``.
    round_method : str, optional
        (*Relative* mode only.)
        The method for rounding the epochs during the splice operation.
        Defaults to ``"floor"``.
    drop_epoch_rnd : bool, optional
        (*Relative* mode only.)
        Whether to drop the rounded epochs during the splice operation.
        Defaults to ``False``.
    rinexmod_options : dict, optional
        The options for modifying the RINEX files during the splice
        operation. Defaults to ``None``.
    metadata : str or list, optional
        The metadata to be included in the spliced RINEX files. Possible
        inputs are:

        * list of string (sitelog file paths),
        * single string (single sitelog file path),
        * single string (directory containing the sitelogs),
        * list of MetaData objects,
        * single MetaData object.

        Defaults to ``None``.

    Returns
    -------
    spc : SpliceGnss
        The SpliceGnss object after the splice operation.
    """
    if not log_dir:
        log_dir = tmp_dir

    # ------------------------------------------------------------------ #
    #  Absolute mode                                                       #
    # ------------------------------------------------------------------ #
    if epoch_srt is not None and epoch_end is not None:
        epo_rng = arocmn.EpochRange(epoch_srt, epoch_end, period, tz="UTC")

        spc = arohdl.SpliceGnss(
            out_dir=out_dir,
            tmp_dir=tmp_dir,
            log_dir=log_dir,
            epoch_range=epo_rng,
            site={'site_id': site},
            session={"data_frequency": data_frequency},
            metadata=metadata,
        )

        spc.splice(
            input_mode="given",
            input_rinexs=rnxs_inp,
            handle_software=handle_software,
            rinexmod_options=rinexmod_options,
        )

        return spc

    # ------------------------------------------------------------------ #
    #  Relative mode                                                       #
    # ------------------------------------------------------------------ #
    epo_rng = arocmn.create_dummy_epochrange(period)

    spc_inp = arohdl.SpliceGnss(
        out_dir=out_dir,
        tmp_dir=tmp_dir,
        log_dir=log_dir,
        epoch_range=epo_rng,
        metadata=metadata,
    )
    spc_inp.load_tab_filelist(rnxs_inp)
    spc_inp.updt_epotab_rnx(use_rnx_filename_only=True)

    spc_main_obj, _ = spc_inp.group_by_epochs(
        period=period,
        rolling_period=rolling_period,
        rolling_ref=rolling_ref,
        round_method=round_method,
        drop_epoch_rnd=drop_epoch_rnd,
    )

    spc_main_obj.splice_core(
        handle_software=handle_software,
        rinexmod_options=rinexmod_options,
    )

    return spc_main_obj
