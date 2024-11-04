#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  8 16:53:51 2024

@author: psakic
"""

import os
import re

import numpy as np
import pandas as pd

from geodezyx import utils
from filelock import FileLock, Timeout

#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv
import autorino.common as arocmn
logger = logging.getLogger(__name__)
logger.setLevel(aroenv.aro_env_dict["general"]["log_level"])

def dummy_site_dic():
    """
    Creates a dummy site dictionary.

    This function creates and returns a dictionary with dummy site information.
    The dictionary contains the following keys:
    - name: The name of the site.
    - site_id: The site identifier.
    - domes: The DOMES number of the site.
    - sitelog_path: The path to the site log.
    - position_xyz: The XYZ coordinates of the site.

    Returns
    -------
    dict
        A dictionary containing dummy site information.
    """
    d = dict()

    d["name"] = "XXXX"
    d["site_id"] = "XXXX00XXX"
    d["domes"] = "00000X000"
    d["sitelog_path"] = "/null"
    d["position_xyz"] = (6378000, 0, 0)

    return d


def dummy_sess_dic():
    """
    Creates a dummy session dictionary.

    This function creates and returns a dictionary with dummy session information.
    The dictionary contains the following keys:
    - name: The name of the session.
    - data_frequency: The data frequency of the session.
    - tmp_dir_parent: The parent directory for temporary files.
    - tmp_dir_structure: The directory structure for temporary files.
    - log_parent_dir: The parent directory for log files.
    - log_dir_structure: The directory structure for log files.
    - out_dir_parent: The parent directory for output files.
    - out_structure: The directory structure for output files.

    Returns
    -------
    dict
        A dictionary containing dummy session information.
    """
    d = dict()

    d["name"] = "NA"
    d["data_frequency"] = "30S"
    d["tmp_dir_parent"] = "<$HOME>/autorino_workflow_tests/tmp"
    d["tmp_dir_structure"] = "<site_id9>/%Y/%j"
    d["log_parent_dir"] = "<$HOME>/autorino_workflow_tests/log"
    d["log_dir_structure"] = "<site_id9>/%Y/%j"
    d["out_dir_parent"] = "<$HOME>/autorino_workflow_tests/out"
    d["out_structure"] = "<site_id9>/%Y/%j"

    return d


def import_files(inp_fil, inp_regex=".*"):
    """
    Handles multiple types of input lists and returns a python list of the input.

    This function can handle various types of input lists and convert them into a python list.
    The input can be:
     * a python list
     * a text file path containing a list of files
     * a tuple containing several text files path
     * a directory path.
    If the input is a directory path, all the files matching the regular expression specified by 'inp_regex' are read.

    Parameters
    ----------
    inp_fil : list or str or tuple
        The input list to be interpreted. It can be a python list, a text file path containing a list of files,
        a tuple containing several text files path, or a directory path.
    inp_regex : str, optional
        The regular expression used to filter the files when 'inp_fil' is a directory path.
        Default is ".*" which matches any file.

    Returns
    -------
    list
        The interpreted list.
    """
    if not inp_fil:
        flist = []
    elif isinstance(inp_fil, tuple) and os.path.isfile(inp_fil[0]):
        flist = list(np.hstack([open(f, "r+").readlines() for f in inp_fil]))
        flist = [f.strip() for f in flist]
    elif isinstance(inp_fil, list):
        flist = inp_fil
    elif os.path.isfile(inp_fil):
        flist = open(inp_fil, "r+").readlines()
        flist = [f.strip() for f in flist]
    elif os.path.isdir(inp_fil):
        flist = utils.find_recursive(inp_fil, inp_regex, case_sensitive=False)
    else:
        flist = []
        logger.warning("the filelist is empty")

    if inp_regex != ".*":
        flist = [f for f in flist if re.match(inp_regex, f)]

    return flist


def load_previous_tables(log_dir):
    """
    Load all previous tables from the log directory.

    This function searches for all files ending with "*table.log" in the log directory
    and concatenates them into a single pandas DataFrame. If no such files are found,
    it returns an empty DataFrame and logs a warning.

    Parameters
    ----------
    log_dir : str
        The directory where the log files are stored.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the concatenated data from all found log files. If no files are found,
        an empty DataFrame is returned.
    """
    # Find all files ending with "*table.log" in the log directory
    tables_files = utils.find_recursive(log_dir, "*_table.log")

    # If no such files are found, log a warning and return an empty DataFrame
    if not tables_files:
        logger.warning("No previous tables found in the log directory.")
        return pd.DataFrame([])
    else:
        # If files are found, read each file into a DataFrame and concatenate them into a single DataFrame
        tab_df_stk = []
        for t in tables_files:
            tab_df = pd.read_csv(t)
            #if not len(tab_df) == 0:
            tab_df_stk.append(tab_df)

        return pd.concat(tab_df_stk)


def is_ok(val_inp):
    """
    Checks if the input value is OK or not.

    This function takes an input value and checks if it is defined.
    It considers None, NaN, False and an empty string as not OK.
    If the input value is one of these, the function returns False. Otherwise, it returns True.

    Parameters
    ----------
    val_inp : any or iterable of any
        The input value to be checked.
        Can handle iterables.

    Returns
    -------
    bool
        True if the input value is defined, False otherwise.
    """

    # iterable case
    typ = utils.get_type_smart(val_inp)

    if utils.is_iterable(val_inp):
        return typ([is_ok(v) for v in val_inp])

    # scalar case
    if val_inp is None:
        return False
    elif isinstance(val_inp, float) and np.isnan(val_inp):
        return False
    elif val_inp == "":
        return False
    elif not val_inp: # == False
        return False
    else:
        return True


def check_lockfile(lockfile_path):
    """
    Checks the lock status of a specified file.

    This function attempts to acquire a lock on the specified file. If the lock is acquired,
    it prints a success message and releases the lock. If the lock is not acquired (i.e., the file
    is already locked by a previous process), it prints a message indicating that the process is locked.

    Parameters
    ----------
    lockfile_path : str
        The path of the lock file to check the lock status for.

    Returns
    -------
    None
    """
    lock = FileLock(lockfile_path)
    try:
        lock.acquire(timeout=0)
        logger.debug(f"Lock free for {lockfile_path}")
        lock.release()
    except Timeout:
        logger.warning(f"Process is locked by a previous process for {lockfile_path}")


def rnxs2step_obj(rnxs_lis_inp):
    """
    Convert a list of RINEX files to a StepGnss object.

    This function creates a StepGnss object and populates it with data from the provided list of RINEX files.
    It loads the table from the file list, updates the site information from the RINEX filenames, and updates
    the epoch table from the RINEX filenames.

    Parameters
    ----------
    rnxs_lis_inp : list
        A list of RINEX file paths to be converted into a StepGnss object.

    Returns
    -------
    StepGnss
        A StepGnss object populated with data from the provided RINEX files.
    """
    stp_obj = arocmn.StepGnss(out_dir="",
                              tmp_dir="",
                              log_dir="",
                              inp_dir="")

    stp_obj.load_tab_filelist(rnxs_lis_inp)
    stp_obj.updt_site_w_rnx_fname()
    stp_obj.updt_epotab_rnx(use_rnx_filename_only=True, update_epoch_range=True)

    return stp_obj