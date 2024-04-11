#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  7 12:07:18 2023

@author: psakic
"""

import os
import re
import numpy as np
import datetime as dt
import dateutil
import docker
from pathlib import Path

from geodezyx import utils, operational

import autorino.common as arocmn
import autorino.convert as arocnv

from rinexmod import rinexmod_api

#### Import the logger
import logging

logger = logging.getLogger(__name__)
logger.setLevel("INFO")


def site_list_from_sitelogs(sitelogs_inp):
    """
    From a list of sitelogs, get a site id list (4 chars)
    """
    ###############################################
    ### read sitelogs
    if not type(sitelogs_inp) is list and os.path.isdir(sitelogs_inp):
        sitelogs = rinexmod_api.sitelog_input_manage(sitelogs_inp,
                                                     force=False)
    else:
        sitelogs = sitelogs_inp

    ### get the site (4chars) as a list
    site4_list = [s.site4char for s in sitelogs]

    return site4_list


def site_search_from_list(fraw_inp, site4_list_inp):
    """
    from a raw file with an approximate site name and a list of correct
    site names, search the correct site name of the raw file
    """
    site_out = None
    for s4 in site4_list_inp:
        if re.search(s4, fraw_inp.name, re.IGNORECASE):
            site_out = s4
            break
    if not site_out:  # last chance, get the 4 1st chars of the raw file
        site_out = fraw_inp.name[:4]
    return site_out


def select_conv_odd_file(fraw_inp,
                          ext_excluded=None):
    """
    do a high level case matching to identify the right converter
    for raw file with an unconventional extension, or exclude the file
    if its extension matches an excluded one
    """

    if ext_excluded is None:
        ext_excluded = [".TG!$",
                        ".DAT",
                        ".Z",
                        ".BCK",
                        "^.[0-9]{3}$",
                        ".A$",
                        "Trimble",
                        ".ORIG"]

    fraw = Path(fraw_inp)
    ext = fraw.suffix.upper()

    if not ext or len(ext) == 0:
        conve = "tps2rin"
    elif re.match(".M[0-9][0-9]", ext):
        conve = "mdb2rinex"
    ### here we skip all the weird files
    else:
        ### per default
        conve = "auto"
        for ext_exl in ext_excluded:
            if re.match(ext_exl, ext):
                conve = None
                logger.warn("%s will be skipped, excluded extention %s",
                            fraw.name,
                            ext_exl)
                break

    return conve


def stop_long_running_containers(max_running_time=120):
    """
    kill Docker container running for a too long time
    Useful for the trm2rinex dockers
    """
    try:
        client = docker.from_env()
    except docker.errors.DockerException:
        logger.warning('Permission denied for Docker')
        return None
    containers = client.containers.list()

    for container in containers:
        ### Calculate the time elapsed since the container was started
        #created_at = container.attrs['Created']
        started_at = container.attrs['State']['StartedAt']

        started_at = dateutil.parser.parse(started_at)
        elapsed_time = dt.datetime.now(dt.timezone.utc) - started_at

        if elapsed_time > dt.timedelta(seconds=max_running_time):
            container.stop()
            logger.warning(f'Stopped container {container.name} after {elapsed_time} seconds.')

    return None