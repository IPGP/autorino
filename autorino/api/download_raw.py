#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 18/09/2024 18:24:17

@author: psakic
"""

import os

import autorino.download as arodwl
import autorino.common as arocmn

#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger("autorino")
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])


def download_raw(
    epoch_srt,
    epoch_end,
    period,
    hostname,
    inp_dir_parent,
    inp_dir_structure,
    inp_file_regex,
    out_dir_parent,
    out_structure="<SITE_ID9>/%Y/",
    site_id="XXXX00XXX",
    login="",
    password="",
    tmp_dir=None,
    log_dir=None,
    options=dict(),
    session=dict(),
):
    """
    Downloads raw GNSS data files.

    This function downloads raw GNSS data files for a specified epoch range and stores them
    in the specified output directory.

    Parameters
    ----------
    epoch_srt : datetime-like
        The start epoch for the splicing operation.
    epoch_end : datetime-like
        The end epoch for the splicing operation.
    period : str
        The period for the splicing operation.
    out_dir_parent : str
        The parent output directory where the downloaded files will be stored.
    out_structure : str
        The structure of the output sub-directory where the downloaded files will be stored.
        Typical values are '<SITE_ID4>/%Y/' or '%Y/%j/'.
        Default value is '<SITE_ID4>/%Y/'.
    hostname : str
        The hostname of the server from which the data files will be downloaded.
    inp_dir_parent : str
        The parent directory on the server where the raw data files are located.
    inp_dir_structure : str
        The raw file generic name structure on the server.
    inp_file_regex : str
        The regular expression used to match the raw data files on the server
    site_id : str, optional
        The site identifier for the data files. Default is "XXXX00XXX".
    login : str, optional
        The login username for the server. Default is an empty string.
    password : str, optional
        The login password for the server. Default is an empty string.
    tmp_dir : str, optional
        The temporary directory used during the download process. Default is None.
    log_dir : str, optional
        The directory where logs will be stored. If not provided, it defaults to tmp_dir. Default is None.
    options : dict, optional
        Additional options for the download process. Default is an empty dictionary.
    session : dict, optional
        Session information for the download process. Default is an empty dictionary.

    Returns
    -------
    object
        The DownloadGnss object after the download operation.
    """

    access_dic = dict()
    access_dic["hostname"] = hostname
    access_dic["login"] = login
    access_dic["password"] = password

    site_dic = dict()
    site_dic["site_id"] = site_id

    epoch_range = arocmn.EpochRange(epoch_srt, epoch_end, period)

    inp_dir = os.path.join(inp_dir_parent, inp_dir_structure)
    out_dir = os.path.join(out_dir_parent, out_structure)

    dwl = arodwl.DownloadGnss(
        out_dir=out_dir,
        tmp_dir=tmp_dir,
        log_dir=log_dir,
        inp_dir=inp_dir,
        inp_file_regex=inp_file_regex,
        epoch_range=epoch_range,
        access=access_dic,
        site=site_dic,
        session=session,
        options=options,
    )

    dwl.download()

    return dwl
