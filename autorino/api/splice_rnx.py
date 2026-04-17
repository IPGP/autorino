#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 18/09/2024 18:26:05

@author: psakic
"""

import os.path

import autorino.handle as arohdl
import autorino.common as arocmn
from geodezyx import utils

#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger("autorino")
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])


def splice_rnx(
    rnxs_inp,
    out_dir,
    tmp_dir,
    period="1d",
    log_dir=None,
    epoch_srt=None,
    epoch_end=None,
    relative_mode=False,
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
    relative_mode : bool, optional
        Explicitly enable *relative* mode.
        If ``True``, ``epoch_srt`` and ``epoch_end`` are ignored (set to
        ``None``), forcing relative mode regardless of their values.
        Defaults to ``False``.
    site : list or str, optional
        site(s) name to be used for the spliced RINEX files (*absolute* mode).
        Facultative but highly recommended to detect existing files to be
        skipped.
        If not site(s) provided, a list of potential sites will be
        automatically detected.
        Defaults to ``None``.
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

    if relative_mode:
        epo_rng = arocmn.dummy_epochrange(period)
        logger.info(">>>>>>>>> Relative-mode splice (experimental)")
    else:
        epo_rng = arocmn.EpochRange(epoch_srt, epoch_end, period, tz="UTC")
        logger.info(">>>>>>>>> Absolute-mode splice")

    # ------------------------------------------------------------------ #
    #  Determine sites                                                   #
    # ------------------------------------------------------------------ #

    inp_dir_use = str(rnxs_inp[0]) if len(rnxs_inp) == 1 else None

    if site:
        sites_use = utils.listify(site)
    elif not site and os.path.isdir(inp_dir_use):
        logger.info("sites will be detected automatically based on the input directory")
        sites_use = arocmn.guess_sites_list(inp_dir_use)
    else:
        logger.error("unable to detect site list. aborting...")
        errmsg = "give site list with 'site' argument or check parent directory (aliases not allowed for site detection): %s"
        logger.error(errmsg, inp_dir_use)
        return None

    for site_use in sites_use:

        logger.info(">>>>>>>>> Splicing site %s", site_use)

        # ------------------------------------------------------------------ #
        #  Determine input RINEXs                                            #
        # ------------------------------------------------------------------ #

        spc_inp_rnx = arohdl.SpliceGnss(
            inp_dir=inp_dir_use,
            out_dir=out_dir,
            tmp_dir=tmp_dir,
            log_dir=log_dir,
            epoch_range=epo_rng,
            site={"site_id": site_use},
            session={"data_frequency": data_frequency},
            metadata=metadata,
        )

        if inp_dir_use:
            inp_mode, inp_rnxs = "find", None
        else:
            inp_mode, inp_rnxs = "given", rnxs_inp

        spc_inp_rnx = spc_inp_rnx.load_input_rnxs(inp_mode, inp_rnxs)

        # ------------------------------------------------------------------ #
        #  Absolute mode                                                     #
        # ------------------------------------------------------------------ #
        if not relative_mode:
            spc_main_obj = arohdl.SpliceGnss(
                out_dir=out_dir,
                tmp_dir=tmp_dir,
                log_dir=log_dir,
                epoch_range=epo_rng,
                site={"site_id": site},
                session={"data_frequency": data_frequency},
                metadata=metadata,
            )

            spc_main_obj.splice(
                input_mode="given",
                input_rinexs=spc_inp_rnx,
                handle_software=handle_software,
                rinexmod_options=rinexmod_options,
            )

        # ------------------------------------------------------------------ #
        #  Relative mode                                                     #
        # ------------------------------------------------------------------ #

        else:
            spc_main_obj, _ = spc_inp_rnx.group_by_epochs(
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

    return None
