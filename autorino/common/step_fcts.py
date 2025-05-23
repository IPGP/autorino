#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  8 16:53:51 2024

@author: psakic
"""

import os
import re
import shutil

import numpy as np
import pandas as pd

from geodezyx import utils, conv
from filelock import FileLock, Timeout

#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv
import autorino.common as arocmn

logger = logging.getLogger("autorino")
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])


def make_site_id9(site_id_inp):
    """
    Converts a site ID to a 9-character format.

    This function takes a site ID and converts it to a 9-character format.
    If the input site ID is already 9 characters long, it returns the uppercase version of the input.
    If the input site ID is 4 characters long, it appends '00XXX' to the uppercase version of the input.
    Otherwise, it takes the first 4 characters of the input, converts them to uppercase, and appends '00XXX'.

    Parameters
    ----------
    site_id_inp : str
        The input site ID to be converted.

    Returns
    -------
    str
        The site ID in 9-character format.
    """
    if len(site_id_inp) == 9:
        return site_id_inp.upper()
    elif len(site_id_inp) == 4:
        return site_id_inp.upper() + "00XXX"
    else:
        return site_id_inp[:4].upper() + "00XXX"

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
    d["tmp_dir_parent"] = "/tmp/"
    d["tmp_dir_structure"] = "<site_id9>/%Y/%j"
    d["log_parent_dir"] = "/tmp/"
    d["log_dir_structure"] = "<site_id9>/%Y/%j"
    d["out_dir_parent"] = "/tmp/"
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
    # the input is a tuple, i.e. a list of text files, the output is the concatenanted content of the text files
    elif isinstance(inp_fil, tuple) and os.path.isfile(inp_fil[0]):
        flist = list(np.hstack([open(f, "r+").readlines() for f in inp_fil]))
        flist = [f.strip() for f in flist]
    # the input is a python list, the output is the same python list
    elif isinstance(inp_fil, list):
        flist = inp_fil
    # the input is a single text file path, the output is the content of the text file
    elif os.path.isfile(inp_fil):
        flist = open(inp_fil, "r+").readlines()
        flist = [f.strip() for f in flist]
    # The input is a directory path, the output is the list of files inside the directory
    elif os.path.isdir(inp_fil):
        # Here we find everything ".*", the regex will be filtered bellow
        flist = utils.find_recursive(inp_fil, ".*", regex=True)
    else:
        flist = []
        logger.warning("the filelist is empty")

    if inp_regex != ".*":
        flist = [f for f in flist if re.match(inp_regex, os.path.basename(f))]
        # os.path.basename is used to match the regex on the filename only

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

    # Read and concatenate non-empty DataFrames from the found files
    tab_df_stk = [pd.read_csv(t) for t in tables_files if not pd.read_csv(t).empty]

    return pd.concat(tab_df_stk, ignore_index=True) if tab_df_stk else pd.DataFrame([])

def print_tab_core(table_inp, max_colwidth=33):
    """
    Prints the table of the StepGnss object with specified formatting.

    This method formats and prints the table of the StepGnss object. It shrinks the strings in the 'fraw',
    'fpath_inp', and 'fpath_out' columns to a specified maximum length and formats the 'epoch_srt' and 'epoch_end'
    columns as strings
    with a specific date-time format. The method then prints the formatted table to the logger.

    Parameters
    ----------
    table_inp : pd.DataFrame
        The input table to be formatted and printed.

    max_colwidth : int, optional
        The maximum column width for the output table. Default is 33.

    Returns
    -------
    str
        The formatted table as a string.
    """

    def _shrink_str(str_inp, maxlen=max_colwidth):
        """
        Shrinks a string to a specified maximum length.

        This function shrinks a string to a specified maximum length by keeping the first and last parts
        of the string and replacing the middle part with '..'.
        The length of the first and last parts is half of the maximum length.

        Parameters
        ----------
        str_inp : str
            The input string to be shrunk.
        maxlen : int, optional
            The maximum length of the output string.
            Default is the value of the 'max_colwidth' parameter of the
            'verbose' method.

        Returns
        -------
        str
            The shrunk string.
        """
        if len(str_inp) <= maxlen:
            return str_inp
        else:
            halflen = int((maxlen / 2) - 1)
            str_out_shrink = str_inp[:halflen] + ".." + str_inp[-halflen:]
            return str_out_shrink

    # we define the FORMATTERS (i.e. functions) for each column
    form = dict()
    form["fraw"] = _shrink_str
    form["fpath_inp"] = _shrink_str
    form["fpath_out"] = _shrink_str

    print_time = lambda t: (
        t.strftime("%y-%m-%d %H:%M:%S") if not pd.isna(t) else "NaT"
    )
    form["epoch_srt"] = print_time
    form["epoch_end"] = print_time

    str_out = table_inp.to_string(max_colwidth=max_colwidth + 1, formatters=form)
    # add +1 in max_colwidth for safety

    return str_out


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
    elif not val_inp:  # == False
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
    stp_obj = arocmn.StepGnss(out_dir="", tmp_dir="", log_dir="", inp_dir="")

    stp_obj.load_tab_filelist(rnxs_lis_inp)
    stp_obj.updt_site_w_rnx_fname()
    stp_obj.updt_epotab_rnx(use_rnx_filename_only=True, update_epoch_range=True)

    return stp_obj


def guess_sites_list(inp_fil):
    """
    Guess the list of sites from the input list.

    This function guesses the list of sites from the input list.
    
    It extracts the site identifier from the input list
    and returns a list of unique site identifiers.

    Parameters
    ----------
    inp_fil : list
        The input list to extract the site identifiers from.
        See `import_files` for details.
        
    Returns
    -------
    list
        A list of unique site identifiers extracted from the input list.
    """
    inp_list = import_files(inp_fil)

    sites_list = []

    for f in inp_list:
        if conv.rinex_regex_search_tester(f, short_name=False):
            site = os.path.basename(f)[:9]
            sites_list.append(site)

    sites_list = list(sorted(list(set(sites_list))))

    return sites_list


def move_copy_core(src, dest, copy_only=False, force=False):
    """
    Moves or copies a file from the source to the destination.

    This function attempts to copy or move a file from the source path to the destination path.
    If the operation is successful, it logs the action and returns the path of the moved/copied file.
    If the operation fails, it logs the error and returns None.

    Parameters
    ----------
    src : str
        The source file path.
    dest : str
        The destination file path.
    copy_only : bool, optional
        If True, the file is copied instead of moved. Default is False.
    force : bool, optional
        Force the move/copy if the file already exists
        Default is False

    Returns
    -------
    str or None
        The path of the moved/copied file if the operation is successful, None otherwise.
    """
    mvcp = "copied" if copy_only else "moved"

    if os.path.isfile(dest) and not force:
        logger.info(f"{dest} exists and kept (force={force})")
        return dest

    try:
        # we prefer a copy rather than a move, mv can lead to some error
        file_moved = shutil.copy2(src, dest)
        file_moved = os.path.abspath(file_moved)
        # file_moved = shutil.move(src, dest)
        logger.debug("file " + mvcp + " to final destination: %s", file_moved)
    except Exception as e:
        logger.error("Error for: %s", src)
        logger.error("Exception raised: %s", e)
        file_moved = None

    if file_moved and (not copy_only) and os.path.isfile(src):
        os.remove(src)

    return file_moved


def log_tester():
    """
    Tests if the logger is working.

    This function checks if the logger is working by logging a test message.
    If the logger is not working, it raises an exception.

    Raises
    ------
    Exception
        If the logger is not working.
    """
    from logging_tree import printout
    printout()

    logger.debug("level debug")
    logger.info("level info")
    logger.warning("level warning")
    logger.error("level error")
    logger.critical("level critical")

    return None
