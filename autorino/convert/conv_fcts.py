#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  7 12:07:18 2023

@author: psakic
"""

import datetime as dt
#### Import the logger
import logging
import os
import re
from pathlib import Path

import dateutil
import docker

from rinexmod import rinexmod_api

logger = logging.getLogger(__name__)
logger.setLevel("INFO")


def site_list_from_metadata(metadata_inp):
    """
    Extracts a list of site IDs from the provided metadata.

    This function takes either a list of metadata objects or a directory path containing metadata files,
    and returns a list of 4-character site IDs extracted from the metadata.

    Parameters
    ----------
    metadata_inp : str or list
    Possible inputs are:
     * list of string (sitelog file paths),
     * single string (single sitelog file path)
     * single string (directory containing the sitelogs)
     * list of MetaData objects
     * single MetaData object

    This function is mainly a wrapper of `rinexmod_api.metadata_input_manage`

    Returns
    -------
    list
        A list of 4-character site IDs extracted from the metadata.

    Notes
    -----
    If `metadata_inp` is a directory path, the function will attempt to read metadata files from the directory.
    """
    ###############################################
    ### read metadata
    if not type(metadata_inp) is list and os.path.isdir(metadata_inp):
        metadata = rinexmod_api.metadata_input_manage(metadata_inp, force=False)
    else:
        metadata = metadata_inp

    ### get the site (4chars) as a list
    site4_list = [s.site4char for s in metadata]
    ### get the site (9chars) as a list
    site9_list = [s.site9char for s in metadata]

    return site4_list, site9_list


def site_search_from_list(fraw_inp, site_list_inp):
    """
    Searches for the correct site name of a raw file from a list of correct site names.

    This function takes a raw file with an approximate site name and a list of correct site names,
    and attempts to find the correct site name of the raw file. If no match is found, it defaults
    to the first 4 characters of the raw file name.

    Parameters
    ----------
    fraw_inp : Path
        The name of the raw file with an approximate site name.
    site_list_inp : list
        A list of correct 4 or 9-character site names.
        Only the 4 first characters will be considered.

    Returns
    -------
    str
        The correct site name of the raw file. If no match is found in the list, the function returns the first 4 characters of the raw file name.

    Notes
    -----
    The function performs a case-insensitive search.
    """

    site_out = None
    for s in site_list_inp:
        s4 = s[:4]
        if re.search(s4, fraw_inp.name, re.IGNORECASE):
            site_out = s
            break
    if not site_out:  # last chance, get the 4 1st chars of the raw file
        site_out = fraw_inp.name[:4]
    return site_out


def select_conv_odd_file(fraw_inp, ext_excluded=None):
    """
    Identifies the right converter for a raw file with an unconventional extension, or excludes the file
    if its extension matches an excluded one.

    This function performs a high-level case matching to determine the appropriate converter for a raw file.
    If the file's extension matches one in the excluded list, the file is skipped.

    See also autorino.conv_cmd_run._convert_select
    for the regular converter selection

    Parameters
    ----------
    fraw_inp : Path
        The name of the raw file with an unconventional extension.
    ext_excluded : list, optional
        A list of file extensions to be excluded. If a file's extension matches one in this list, the file is skipped.
        Default is [".TG!$", ".DAT", ".Z", ".BCK", "^.[0-9]{3}$", ".A$", "Trimble", ".ORIG"].

    Returns
    -------
    str
        The name of the appropriate converter for the raw file. If the file is to be skipped, returns None.

    Notes
    -----
    The function uses regular expressions to match file extensions.
    """
    if ext_excluded is None:
        ext_excluded = [
            ".TG!$",
            ".DAT",
            ".Z",
            ".BCK",
            "^.[0-9]{3}$",
            ".A$",
            "Trimble",
            ".ORIG",
        ]

    fraw = Path(fraw_inp)
    ext = fraw.suffix.upper()

    if not ext or len(ext) == 0:
        conve = "tps2rin"
    elif re.match(".M[0-9][0-9]", ext):
        conve = "mdb2rinex"
    else:
        conve = "auto"
        for ext_exl in ext_excluded:
            if re.match(ext_exl, ext):
                conve = None
                logger.warn(
                    "%s will be skipped, excluded extention %s", fraw.name, ext_exl
                )
                break

    return conve


def stop_long_running_containers(max_running_time=120):
    """
    Stops Docker containers that have been running for a specified amount of time.

    This function is useful for stopping long-running trm2rinex Docker containers.
    It iterates over all running Docker containers and stops any that have been running for longer than the specified maximum running time.

    Parameters
    ----------
    max_running_time : int, optional
        The maximum running time (in seconds) for a Docker container. Any container running longer than this will be stopped. Default is 120 seconds.

    Returns
    -------
    None

    Raises
    ------
    docker.errors.DockerException
        If permission is denied for Docker.

    Notes
    -----
    The function uses the Docker Python SDK to interact with Docker containers.
    """
    try:
        client = docker.from_env()
    except docker.errors.DockerException:
        logger.warning("Permission denied for Docker")
        return None
    containers = client.containers.list()

    for container in containers:
        # Calculate the time elapsed since the container was started
        started_at = container.attrs["State"]["StartedAt"]
        started_at = dateutil.parser.parse(started_at)
        elapsed_time = dt.datetime.now(dt.timezone.utc) - started_at

        if elapsed_time > dt.timedelta(seconds=max_running_time):
            container.stop()
            logger.warning(
                f"Stopped container {container.name} after {elapsed_time} seconds."
            )

    return None
