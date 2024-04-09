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


class ConvertGnss(arocmn.StepGnss):
    def __init__(self, out_dir, tmp_dir, log_dir,
                 epoch_range=None,
                 site=None,
                 session=None,
                 sitelogs=None,
                 options=None):

        super().__init__(out_dir, tmp_dir, log_dir,
                         epoch_range=epoch_range,
                         site=site,
                         session=session,
                         options=options)

        ### temp dirs init
        self._init_tmp_dirs_paths()

        ### sitelog init
        if sitelogs:
            sitelogs_set = self.translate_path(sitelogs)
            self.sitelogs = rinexmod_api.sitelog_input_manage(sitelogs_set,
                                                              force=False)
        else:
            self.sitelogs = None

    ###############################################

    def convert(self, print_table=False, force=False,
                rinexmod_options=None):
        logger.info("******** RAW > RINEX files conversion / Header mod ('rinexmod')")

        if not rinexmod_options:
            rinexmod_options = {'compression': "gz",
                                'longname': True,
                                'force_rnx_load': True,
                                'verbose': False,
                                'tolerant_file_period': True,
                                'full_history': True}

        if self.sitelogs:
            site4_list = site_list_from_sitelogs(self.sitelogs)
        else:
            site4_list = []

        tmp_dir_logs_use, _, _, _ = self.set_tmp_dirs_paths()

        ### initialize the table as log
        self.set_table_log(out_dir=tmp_dir_logs_use)
        ### initialize list for tmp rinexs to be removed
        frnxtmp_files = []

        ### guess and deactivate existing local RINEX files
        if not force:
            self.guess_local_rnx_files()
            self.check_local_files()
            self.filter_ok_out()

        self.tmp_decmp_files = self.decompress()

        ### get a table with only the good files (ok_inp == True)
        # table_init_ok must be used only for the following statistics!
        table_init_ok = self.filter_purge()
        n_ok_inp = (self.table['ok_inp']).sum()
        n_not_ok_inp = np.logical_not(self.table['ok_inp']).sum()

        logger.info("%6i files will be converted, %6i files are excluded",
                    n_ok_inp, n_not_ok_inp)

        if print_table:
            self.print_table()

        ######################### START THE LOOP ##############################
        for irow, row in self.table.iterrows():
            fraw = Path(row['fpath_inp'])
            ext = fraw.suffix.lower()

            if not self.table.loc[irow, 'ok_inp'] and self.table.loc[irow, 'ok_out']:
                logger.info("conversion skipped (output already exists): %s", fraw)
                continue
            if not self.table.loc[irow, 'ok_inp']:
                logger.warning("conversion skipped (something went wrong): %s", fraw)
                continue

            logger.info("***** input raw file for conversion: %s",
                        fraw.name)

            _, tmp_dir_unzipped_use, tmp_dir_converted_use, tmp_dir_rinexmoded_use = self.set_tmp_dirs_paths()

            ### since the site code from fraw can be poorly formatted
            # we search it w.r.t. the sites from the sitelogs
            site = _site_search_from_list(fraw,
                                          site4_list)

            ### do a first converter selection by removing odd files 
            conve = _select_conv_odd_file(fraw)

            logger.info("extension/converter: %s/%s", ext, conve)

            if not conve:
                logger.info("file skipped, no converter found: %s", fraw)
                self.table.loc[irow, 'note'] = "no converter found"
                self.table.loc[irow, 'ok_inp'] = False
                self.write_in_table_log(self.table.loc[irow])

            ### a function to stop the docker containers running for too long
            # (for trimble conversion)
            stop_long_running_containers()

            #############################################################
            ###### CONVERSION
            frnxtmp = self.on_row_convert(irow, tmp_dir_converted_use,
                                          converter_inp=conve)
            self.tmp_rnx_files.append(frnxtmp)  ### list for final remove
            ### NO MORE EXCEPTION HERE FOR THE MOMENT !!!!!

            #############################################################
            ###### RINEXMOD
            rinexmod_kwargs = rinexmod_options.copy()
            rinexmod_kwargs.update({'marker':site,
                                    'sitelog':self.sitelogs})

            self.on_row_rinexmod(irow, tmp_dir_rinexmoded_use, rinexmod_kwargs)
            ### NO MORE EXCEPTION HERE FOR THE MOMENT !!!!!

            #############################################################
            ###### FINAL MOVE
            self.on_row_move_final(irow)
            ### NO MORE EXCEPTION HERE FOR THE MOMENT !!!!!

        #### remove temporary files

        self.remove_tmp_files()

        return None

    #               _   _
    #     /\       | | (_)
    #    /  \   ___| |_ _  ___  _ __  ___    ___  _ __    _ __ _____      _____
    #   / /\ \ / __| __| |/ _ \| '_ \/ __|  / _ \| '_ \  | '__/ _ \ \ /\ / / __|
    #  / ____ \ (__| |_| | (_) | | | \__ \ | (_) | | | | | | | (_) \ V  V /\__ \
    # /_/    \_\___|\__|_|\___/|_| |_|___/  \___/|_| |_| |_|  \___/ \_/\_/ |___/
    #

    def on_row_convert(self, irow, out_dir_inp, converter_inp):

        if not self.table.loc[irow, 'ok_inp']:
            logger.warning("action on row skipped (input disabled): %s",
                           self.table.loc[irow, 'fname'])
            return None

        frnxtmp, _ = arocnv.converter_run(self.table.loc[irow, 'fpath_inp'],
                                          out_dir_inp,
                                          converter=converter_inp)
        if frnxtmp:
            ### update table if things go well
            self.table.loc[irow, 'fpath_out'] = frnxtmp
            epo_srt_ok, epo_end_ok = operational.rinex_start_end(frnxtmp)
            self.table.loc[irow, 'epoch_srt'] = epo_srt_ok
            self.table.loc[irow, 'epoch_end'] = epo_end_ok
            self.table.loc[irow, 'ok_out'] = True
        else:
            ### update table if things go wrong
            self.table.loc[irow, 'ok_out'] = False
        return frnxtmp

 

#########################################################################
#### Misc functions 

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


def _site_search_from_list(fraw_inp, site4_list_inp):
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


def _select_conv_odd_file(fraw_inp,
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