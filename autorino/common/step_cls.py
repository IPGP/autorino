#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  8 16:53:51 2024

@author: psakic
"""

import copy

import os
import re
import shutil
import time
from filelock import FileLock, Timeout


import numpy as np
import pandas as pd

import autorino.common as arocmn
import autorino.cfglog as arologcfg
import rinexmod

from geodezyx import utils, conv
from rinexmod import rinexmod_api

#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger(__name__)
logger.setLevel(aroenv.aro_env_dict["general"]["log_level"])


class StepGnss:
    """
    The StepGnss class represents a step in a GNSS processing chain. It contains methods for initializing and managing
    various aspects of a processing step, including epoch ranges, sites, sessions, options, and metadata. It also provides
    methods for handling temporary directories, logging, and table management.

    Attributes
    ----------
    out_dir : str
        The output directory for the step.
    tmp_dir : str
        The temporary directory for the step.
    log_dir : str
        The log directory for the step.
    epoch_range : EpochRange
        The epoch range for the step.
    site : dict
        The site information for the step.
    session : dict
        The session information for the step.
    options : dict
        The options for the step.
    metadata : dict
        The metadata for the step.
    """

    def __init__(
        self,
        out_dir,
        tmp_dir,
        log_dir,
        epoch_range=None,
        site=None,
        session=None,
        options=None,
        metadata=None,
    ):
        """
        Initializes a new instance of the StepGnss class.

        Parameters
        ----------
        out_dir : str
            The output directory for the step.
        tmp_dir : str
            The temporary directory for the step.
        log_dir : str
            The log directory for the step.
        epoch_range : EpochRange, optional
            The epoch range for the step. If not provided, a dummy epoch range is created.
        site : dict, optional
            The site information for the step. If not provided, a dummy site is created.
        session : dict, optional
            The session information for the step. If not provided, a dummy session is created.
        options : dict, optional
            The options for the step. If not provided, an empty options dictionary is created.
        metadata : str or list, optional
            The metadata to be included in the converted RINEX files. Possible inputs are:
             * list of string (sitelog file paths),
             * single string (single sitelog file path)
             * single string (directory containing the sitelogs)
             * list of MetaData objects
             * single MetaData object.
             Defaults to None.
        """
        self._init_epoch_range(epoch_range)
        self._init_site(site)
        self._init_session(session)
        self._init_options(options)
        self._init_site_id()
        self._init_table()

        self.set_translate_dict()

        ### sitelog init (needs translate dict)
        self._init_metadata(metadata)

        self.out_dir = out_dir
        self.tmp_dir = tmp_dir
        self.log_dir = log_dir

        ### temp dirs init
        self._init_tmp_dirs_paths()

        # generic log
        self.set_logfile()
        # table log is on request only (for the moment9)
        # thus this table_log_path attribute must be initialized as none
        self.table_log_path = None

        #### list to stack temporarily the temporary files before their delete
        self.tmp_rnx_files = []
        self.tmp_decmp_files = []

    def __repr__(self):
        name = type(self).__name__
        out = "{} {}/{}".format(name, self.site_id, self.epoch_range)
        return out

    # getter and setter
    # site_id

    @property
    def out_dir(self):
        return self.translate_path(self._out_dir)

    @out_dir.setter
    def out_dir(self, value):
        self._out_dir = value

    @property
    def tmp_dir(self):
        return self.translate_path(self._tmp_dir)

    @tmp_dir.setter
    def tmp_dir(self, value):
        self._tmp_dir = value

    @property
    def log_dir(self):
        return self.translate_path(self._log_dir)

    @log_dir.setter
    def log_dir(self, value):
        self._log_dir = value

    ### site
    @property
    def site_id(self):
        return self._site_id

    @site_id.setter
    def site_id(self, value):
        self._site_id = value

    @property
    def site_id4(self):
        return self._site_id[:4]

    @property
    def site_id9(self):
        if len(self._site_id) == 9:
            return self._site_id
        elif len(self._site_id) == 4:
            return self._site_id + "00XXX"
        else:
            return self._site_id[:4] + "00XXX"

    # epoch_range
    @property
    def epoch_range(self):
        return self._epoch_range

    @epoch_range.setter
    def epoch_range(self, value):
        self._epoch_range = value

    # table
    @property
    def table(self):
        return self._table

    @table.setter
    def table(self, value):
        self._table = value
        # designed for future safety tests

    def _init_table(self, table_cols: list = None, init_epoch: bool = True):
        """
        Initializes the table of a StepGnss object.

        This method creates a new pandas DataFrame with specified columns. If no columns are provided,
        it creates a DataFrame with default columns. If `init_epoch` is True, it also initializes the
        'epoch_srt' and 'epoch_end' columns with the epoch range of the StepGnss object and the 'site'
        column with the site ID of the StepGnss object.

        Parameters
        ----------
        table_cols : list of str, optional
            The columns to include in the table. If not provided, default columns are used.
        init_epoch : bool, optional
            If True, initializes the 'epoch_srt' and 'epoch_end' columns with the epoch range of the
            StepGnss object and the 'site' column with the site ID of the StepGnss object. Default is True.

        Returns
        -------
        None
        """
        if table_cols is None:
            table_cols = [
                "fname",
                "site",
                "epoch_srt",
                "epoch_end",
                "ok_inp",
                "ok_out",
                "fpath_inp",
                "fpath_out",
                "size_inp",
                "size_out",
                "note",
            ]

        df = pd.DataFrame([], columns=table_cols)

        if init_epoch:
            df["epoch_srt"] = self.epoch_range.epoch_range_list()
            df["epoch_end"] = self.epoch_range.epoch_range_list(end_bound=True)

            df["site"] = self.site_id

        self.table = df
        return None

    def _init_site(self, site):
        """
        Initializes the site attribute of the StepGnss object.

        If a site dictionary is not provided, a warning is logged and a dummy site dictionary is created and set as the
        site attribute.
        If a site dictionary is provided, it is set as the site attribute.

        Parameters
        ----------
        site : dict, optional
            The site information for the step. If not provided, a dummy site is created.

        Returns
        -------
        None
        """
        if not site:
            logger.warning("no site dict given, a dummy one will be created")
            self.site = arocmn.create_dummy_site_dic()
        else:
            self.site = site

        return None

    def _init_session(self, session):
        """
        Initializes the session attribute of the StepGnss object.

        If a session dictionary is not provided, a warning is logged and a dummy session dictionary is created
        and set as the session attribute.
        If a session dictionary is provided, it is set as the session attribute.

        Parameters
        ----------
        session : dict, optional
            The session information for the step. If not provided, a dummy session is created.

        Returns
        -------
        None
        """
        if not session:
            logger.warning("no session dict given, a dummy one will be created")
            self.session = arocmn.create_dummy_session_dic()
        else:
            self.session = session

        return None

    def _init_options(self, options):
        """
        Initializes the options attribute of the StepGnss object.

        This method sets the options attribute of the StepGnss object. If an options dictionary is not provided,
        it creates an empty dictionary and sets it as the options attribute.

        Parameters
        ----------
        options : dict, optional
            The options for the step. If not provided, an empty dictionary is created.

        Returns
        -------
        None
        """
        if not options:
            self.options = {}
        else:
            self.options = options

        return None

    def _init_site_id(self):
        """
        Initializes the site_id attribute of the StepGnss object.

        This method checks if a 'site_id' is provided in the site dictionary.
        If it is, it sets the 'site_id' attribute of the StepGnss object to the provided 'site_id'.
        If a 'site_id' is not provided, it sets the 'site_id' attribute to 'XXXX00XX00XXXX' as a default value.

        Returns
        -------
        None
        """
        if "site_id" in self.site.keys():
            self.site_id = self.site["site_id"]
        else:
            self.site_id = "XXXX00XXX"

        return None

    def _init_epoch_range(self, epoch_range):
        """
        Initializes the epoch range of the StepGnss object.

        This method sets the epoch range of the StepGnss object.
        If an epoch range is provided, it interprets the epoch range using the `epoch_range_interpret` function
        from the `arocmn` module.
        If an epoch range is not provided, it creates a dummy epoch range between 'NaT' (not a time) using
        the `EpochRange` function from the `arocmn` module.

        Parameters
        ----------
        epoch_range : str, optional
            The epoch range for the step. If not provided, a dummy epoch range is created.

        Returns
        -------
        None
        """
        if epoch_range:
            self.epoch_range = arocmn.epoch_range_interpret(epoch_range)
        else:
            self.epoch_range = arocmn.EpochRange(pd.NaT, pd.NaT)

        return None

    def set_translate_dict(self):
        """
        Generates the translation dictionary based on the site and session dictionaries,
        object attributes, and site id.

        The translation dictionary is used to replace placeholders in the path strings with actual values.
        It includes keys for each attribute in the site and session dictionaries, as well as for the site id.
        The site id has three variations: 'site_id', 'site_id4', and 'site_id9', each in both lower and upper case.

        The method does not take any parameters and does not return any value.
        It directly modifies the 'translate_dict' attribute of the object.

        Returns
        -------
        None
        """
        trsltdict = dict()

        # Add each attribute from the site and session dictionaries to the translation dictionary
        for dic in (self.site, self.session):
            for k, v in dic.items():
                trsltdict[k] = v

        # Add each variation of the site id to the translation dictionary
        for s in ("site_id", "site_id4", "site_id9"):
            trsltdict[s.upper()] = str(getattr(self, s)).upper()
            trsltdict[s.lower()] = str(getattr(self, s)).lower()

        # Update the translate_dict attribute of the object
        self.translate_dict = trsltdict

        return None

    def _init_tmp_dirs_paths(
        self,
        tmp_subdir_logs="logs",
        tmp_subdir_unzip="unzipped",
        tmp_subdir_conv="converted",
        tmp_subdir_rnxmod="rinexmoded",
        tmp_subdir_dwnld="downloaded",
    ):
        """
        Initializes the temporary directories paths for the StepGnss object.

        This method sets the paths for the temporary directories of the StepGnss object. It creates the paths in a generic form, with placeholders and without creating the actual directories.
        The directories include logs, unzipped, converted, rinexmoded, and downloaded directories.

        Parameters
        ----------
        tmp_subdir_logs : str, optional
            The subdirectory for logs. Default is 'logs'.
        tmp_subdir_unzip : str, optional
            The subdirectory for unzipped files. Default is 'unzipped'.
        tmp_subdir_conv : str, optional
            The subdirectory for converted files. Default is 'converted'.
        tmp_subdir_rnxmod : str, optional
            The subdirectory for rinexmoded files. Default is 'rinexmoded'.
        tmp_subdir_dwnld : str, optional
            The subdirectory for downloaded files. Default is 'downloaded'.

        Returns
        -------
        None
        """
        # Internal versions have not been translated
        self._tmp_dir_logs = os.path.join(self.tmp_dir, tmp_subdir_logs)
        self._tmp_dir_unzipped = os.path.join(self.tmp_dir, tmp_subdir_unzip)
        self._tmp_dir_converted = os.path.join(self.tmp_dir, tmp_subdir_conv)
        self._tmp_dir_rinexmoded = os.path.join(self.tmp_dir, tmp_subdir_rnxmod)
        self._tmp_dir_downloaded = os.path.join(self.tmp_dir, tmp_subdir_dwnld)

        # Translation of the paths
        self.tmp_dir_logs = self.translate_path(self._tmp_dir_logs)
        self.tmp_dir_unzipped = self.translate_path(self._tmp_dir_unzipped)
        self.tmp_dir_converted = self.translate_path(self._tmp_dir_converted)
        self.tmp_dir_rinexmoded = self.translate_path(self._tmp_dir_rinexmoded)
        self.tmp_dir_downloaded = self.translate_path(self._tmp_dir_downloaded)

        return None

    def set_tmp_dirs(self):
        """
        Translates and creates temporary directories.

        This method translates the paths of the temporary directories and creates them if they do not exist.
        The directories include logs, unzipped, converted, rinexmoded, and downloaded directories.
        The paths are translated using the `translate_path` method of the StepGnss object, which replaces placeholders
        in the paths with actual values.
        The directories are created if the `make_dir` parameter of the `translate_path` method is set to True.

        Note: This translation is also done in the `_init_tmp_dirs_paths` method, but it is redone here
        to ensure accuracy.

        Returns
        -------
        tuple
            A tuple containing the paths of the logs, unzipped, converted, rinexmoded, and downloaded directories,
            in that order.
        """
        # This translation is also done in _init_tmp_dirs_paths
        # but we redo it here, simply to be sure
        tmp_dir_logs_set = self.translate_path(self._tmp_dir_logs, make_dir=True)
        tmp_dir_unzipped_set = self.translate_path(
            self._tmp_dir_unzipped, make_dir=True
        )
        tmp_dir_converted_set = self.translate_path(
            self._tmp_dir_converted, make_dir=True
        )
        tmp_dir_rinexmoded_set = self.translate_path(
            self._tmp_dir_rinexmoded, make_dir=True
        )
        tmp_dir_downloaded_set = self.translate_path(
            self._tmp_dir_downloaded, make_dir=True
        )

        return (
            tmp_dir_logs_set,
            tmp_dir_unzipped_set,
            tmp_dir_converted_set,
            tmp_dir_rinexmoded_set,
            tmp_dir_downloaded_set,
        )

    def clean_tmp_dirs(self, days=7, keep_table_logs=True):
        """
        Cleans the temporary directories of the StepGnss object than a specified number of days in the temporary
        directories of the StepGnss object.

        This method removes all files in the temporary directories of the StepGnss object that are older than the
        specified number of days.
        The directories include logs, unzipped, converted, rinexmoded, and downloaded directories.

        See Also remove_tmp_files(), which clean the files in the temporary directories at the end of the processing
        based on ad hoc lists.

        Parameters
        ----------
        days : int, optional
            The number of days to use as the threshold for deleting old files. Default is 2 days.

        Returns
        -------
        None
        """

        current_time = time.time()
        age_threshold = days * 86400  # Convert days to seconds

        # Iterate through the temporary directories
        for tmp_dir in [
            self.tmp_dir_logs,
            self.tmp_dir_unzipped,
            self.tmp_dir_converted,
            self.tmp_dir_rinexmoded,
            self.tmp_dir_downloaded,
        ]:
            if os.path.isdir(tmp_dir):
                for root, dirs, files in os.walk(tmp_dir):
                    for file in files:
                        if keep_table_logs and file.endswith("table.log"):
                            continue
                        file_path = os.path.join(root, file)
                        file_age = current_time - os.path.getmtime(file_path)
                        if file_age > age_threshold:
                            os.remove(file_path)
                            logger.debug("Deleted old file: %s", file_path)

        return None

    def _init_metadata(self, metadata):
        """
        Initializes the metadata attribute of the StepGnss object.

        This method checks if a 'metadata' is provided. If it is, it translates the path of the metadata,
        manages the site log input using the `metadata_input_manage` function from the `rinexmod_api` module,
        and sets the 'metadata' attribute of the StepGnss object to the managed site log input.
        If a 'metadata' is not provided, it sets the 'metadata' attribute to None.

        Parameters
        ----------
        metadata : str, optional
            The metadata for the step. If not provided, the 'metadata' attribute is set to None.

        Returns
        -------
        None
        """
        if metadata:
            metadata_set = self.translate_path(metadata)
            self.metadata = rinexmod_api.metadata_input_manage(
                metadata_set, force=False
            )
        else:
            self.metadata = None

    #   _____                           _                  _   _               _
    #  / ____|                         | |                | | | |             | |
    # | |  __  ___ _ __   ___ _ __ __ _| |  _ __ ___   ___| |_| |__   ___   __| |___
    # | | |_ |/ _ \ '_ \ / _ \ '__/ _` | | | '_ ` _ \ / _ \ __| '_ \ / _ \ / _` / __|
    # | |__| |  __/ | | |  __/ | | (_| | | | | | | | |  __/ |_| | | | (_) | (_| \__ \
    #  \_____|\___|_| |_|\___|_|  \__,_|_| |_| |_| |_|\___|\__|_| |_|\___/ \__,_|___/

    def copy(self):
        """
        Creates a duplicate of the current StepGnss object.

        This method uses the deepcopy function from the copy module to create a new instance of the StepGnss class that is a
        complete copy of the current instance. All attributes of the current instance are copied to the new instance.

        Returns
        -------
        StepGnss
            A new instance of the StepGnss class that is a copy of the current instance.
        """
        return copy.deepcopy(self)

    def get_step_type(self, full_object_name=False):
        """
        Returns the type of the step as a string.

        This method is used to identify the type of the current step in the GNSS processing chain.
        It returns the name of the class to which the current instance belongs. If the 'full_object_name'
        parameter is False, it returns a shortened version of the class name, in lower case and without
        the 'Gnss' suffix.

        Parameters
        ----------
        full_object_name : bool, optional
            If True, the full name of the class is returned. If False, a shortened version of the class name,
            in lower case, and without the 'Gnss' suffix.
            Default is False.

        Returns
        -------
        str
            The name of the class to which the current instance belongs. If 'full_object_name' is False,
            the last 4 characters are removed from the class name.
        """
        if full_object_name:
            return type(self).__name__
        else:
            return type(self).__name__[:-4].lower()

    def update_epoch_table_from_rnx_fname(
        self, use_rnx_filename_only=False, update_epoch_range=True
    ):
        """
        Updates the StepGnss table's columns 'epoch_srt' and 'epoch_end' based on the RINEX files.

        If the StepGnss object contains RINEX files, this function updates the 'epoch_srt' and 'epoch_end' columns
        of the StepGnss table based on the RINEX files. The start and end epochs and the period of the RINEX file
        can be determined based on its name only (if use_rnx_filename_only is True). This function is much faster
        but less reliable. At the end of the table update, it can also update the EpochRange object associated to
        the StepGnss object (if update_epoch_range is True).

        Parameters
        ----------
        use_rnx_filename_only : bool, optional
            If True, determines the start epoch, the end epoch and the period of the RINEX file based on its name only.
            The RINEX file is not read. This function is much faster but less reliable. Default is False.
        update_epoch_range : bool, optional
            If True, at the end of the table update, also updates the EpochRange object associated to
            the StepGnss object.
            This is recommended. Default is True.

        Returns
        -------
        None
        """
        is_rnx = self.table["fname"].apply(conv.rinex_regex_search_tester).apply(bool)

        if is_rnx.sum() == 0:
            logger.warning(
                "epoch update impossible, no file matches a RINEX pattern in %s", self
            )
            return

        for irow, row in self.table.iterrows():
            if not use_rnx_filename_only:
                rnx = rinexmod.rinexfile.RinexFile(row["fpath_inp"])
                epo_srt = rnx.start_date
                epo_end = rnx.end_date
            else:
                epo_srt, epo_end, _ = rinexmod.rinexfile.dates_from_rinex_filename(
                    row["fpath_inp"]
                )

            self.table.loc[irow, "epoch_srt"] = epo_srt
            self.table.loc[irow, "epoch_end"] = epo_end

        self.table["epoch_srt"] = pd.to_datetime(self.table["epoch_srt"])
        self.table["epoch_end"] = pd.to_datetime(self.table["epoch_end"])

        if update_epoch_range:
            logger.info(
                "update the epoch range from %i RINEX filenames", len(self.table)
            )
            self.update_epoch_range_from_table()

        return None

    def update_epoch_range_from_table(
        self, column_srt="epoch_srt", column_end="epoch_end"
    ):
        """
        Updates the EpochRange of the StepGnss object based on the min/max epochs in the object's table.

        This function calculates the minimum and maximum epochs from the specified columns in the table.
        It then calculates the most common period (time difference between start and end epochs) in the table.
        The function updates the EpochRange of the StepGnss object with these calculated values.

        Parameters
        ----------
        column_srt : str, optional
            The name of the column in the table that contains the start epochs. Default is 'epoch_srt'.
        column_end : str, optional
            The name of the column in the table that contains the end epochs. Default is 'epoch_end'.

        Notes
        -----
        If the period spacing in the table is not uniform, the function will keep the most common period.
        """
        epomin = self.table[column_srt].min()
        epomax = self.table[column_srt].max()

        epoch1 = epomin
        epoch2 = epomax

        tdelta = self.table[column_end] - self.table[column_srt]

        n_tdelta = tdelta.value_counts().to_frame()
        v_tdelta = tdelta.mode()[0]

        if len(n_tdelta) > 1:
            logger.warning(
                "the period spacing of %s is not uniform, keep the most common", self
            )
            logger.warning("%s", n_tdelta)
            # be sure to keep the 1st one!!!

        period_new = arocmn.timedelta2freq_alias(v_tdelta)
        # logger.debug("new period, %s, %s", v_tdelta, period_new)

        self.epoch_range = arocmn.EpochRange(
            epoch1,
            epoch2,
            period_new,
            round_method=self.epoch_range.round_method,
            tz=self.epoch_range.tz,
        )

        logger.debug("new %s for %s", self.epoch_range, str(self).split("/")[0])

    def translate_path(
        self, path_inp: str, epoch_inp=None, make_dir: bool = False
    ) -> str:
        """
        Translates a given path using the object's translation dictionary and optionally creates the directory.

        This function is able to create a directory corresponding to the translated path if `make_dir` is True.
        Warning: it creates the directory as it is! (no dirname extraction)
        If the translated path is a full path with a filename, you will get nasty results!

        Parameters
        ----------
        path_inp : str
            The input path to be translated.
        epoch_inp : str, optional
            The epoch input to be used in the translation. Default is None.
        make_dir : bool, optional
            If True, the function will create the directory corresponding to the translated path. Default is False.

        Returns
        -------
        str
            The translated directory path.

        Notes
        -----
        The function uses the `translator` function from the `arocmn` module to perform the translation.
        """
        trslt_dir = arocmn.translator(path_inp, self.translate_dict, epoch_inp)
        if make_dir and not os.path.isdir(trslt_dir):
            utils.create_dir(trslt_dir)
            logger.debug("directory created: %s", trslt_dir)
        return trslt_dir

    def create_lockfile(self, timeout=1800, prefix_lockfile=None):
        """
        Creates a lock file for the specified file path.

        This method attempts to acquire a lock on the specified file. If the lock is acquired,
        it prints a success message.
        If the lock is not acquired (i.e., the file is already locked),
        it prints a message indicating that the process is locked.

        Parameters
        ----------
        timeout : int, optional
            The timeout period in seconds to wait for acquiring the lock. Default is 1800 seconds.
        prefix_lockfile : str, optional
            The prefix to use for the lock file name. If not provided, a random integer is used.

        Returns
        -------
        FileLock
            The FileLock object representing the lock on the file.
        """

        if not prefix_lockfile:
            prefix_lockfile = str(np.random.randint(100000, 999999))

        if hasattr(self, "access"):
            if isinstance(self.access, dict) and "network" in self.access:
                prefix_lockfile = self.access["network"]

        lockfile_path = os.path.join(self.tmp_dir, prefix_lockfile + "_lock")

        # a preliminary check to see if a previous lock exists
        arocmn.check_lockfile(lockfile_path)

        lock = FileLock(lockfile_path)

        try:
            lock.acquire(timeout=timeout)
            logger.info(f"Lock acquired for {lockfile_path}")
        except Timeout:
            logger.error(
                f"Process still locked after {timeout} s for {lockfile_path}, aborting"
            )

        return lock

    #  _                       _
    # | |                     (_)
    # | |     ___   __ _  __ _ _ _ __   __ _
    # | |    / _ \ / _` |/ _` | | '_ \ / _` |
    # | |___| (_) | (_| | (_| | | | | | (_| |
    # |______\___/ \__, |\__, |_|_| |_|\__, |
    #               __/ | __/ |         __/ |
    #              |___/ |___/         |___/

    def set_logfile(self, log_dir_inp=None, step_suffix=""):
        """
        set logging in a file
        """

        if not log_dir_inp:
            log_dir = self.log_dir
            if not os.path.isdir(log_dir):
                self.set_tmp_dirs()
        else:
            log_dir = log_dir_inp

        log_dir_use = self.translate_path(log_dir)

        _logger = logging.getLogger("autorino")

        ts = utils.get_timestamp()
        log_name = "_".join((ts, step_suffix, ".log"))
        log_path = os.path.join(log_dir_use, log_name)

        log_cfg_dic = arologcfg.log_config_dict
        fmt_dic = log_cfg_dic["formatters"]["fmtgzyx_nocolor"]

        logfile_handler = logging.FileHandler(log_path)

        fileformatter = logging.Formatter(**fmt_dic)

        logfile_handler.setFormatter(fileformatter)
        logfile_handler.setLevel("DEBUG")

        # the root logger
        # https://stackoverflow.com/questions/48712206/what-is-the-name-of-pythons-root-logger
        # the heritage for loggers
        # https://stackoverflow.com/questions/29069655/python-logging-with-a-common-logger-class-mixin-and-class-inheritance
        _logger.addHandler(logfile_handler)

        return logfile_handler

    def set_table_log(self, out_dir=None, step_suffix=""):
        if not out_dir:
            out_dir = self.tmp_dir

        ts = utils.get_timestamp()
        talo_name = "_".join((ts, step_suffix, "table.log"))
        talo_path = os.path.join(out_dir, talo_name)

        # initalize with a void table
        talo_df_void = pd.DataFrame([], columns=self.table.columns)
        talo_df_void.to_csv(talo_path, mode="w", index=False)

        # if self.table_log_path:
        self.table_log_path = talo_path

        return talo_path

    def write_in_table_log(self, row_in):
        pd.DataFrame(row_in).T.to_csv(
            self.table_log_path, mode="a", index=False, header=False
        )
        return None

    #  _______    _     _                                                                    _
    # |__   __|  | |   | |                                                                  | |
    #    | | __ _| |__ | | ___   _ __ ___   __ _ _ __   __ _  __ _  ___ _ __ ___   ___ _ __ | |_
    #    | |/ _` | '_ \| |/ _ \ | '_ ` _ \ / _` | '_ \ / _` |/ _` |/ _ \ '_ ` _ \ / _ \ '_ \| __|
    #    | | (_| | |_) | |  __/ | | | | | | (_| | | | | (_| | (_| |  __/ | | | | |  __/ | | | |_
    #    |_|\__,_|_.__/|_|\___| |_| |_| |_|\__,_|_| |_|\__,_|\__, |\___|_| |_| |_|\___|_| |_|\__|
    #                                                         __/ |
    #                                                        |___/

    def print_table(self, no_print=False, no_return=True, max_colwidth=33):
        """
        Prints the table of the StepGnss object with specified formatting.

        This method formats and prints the table of the StepGnss object. It shrinks the strings in the 'fraw',
        'fpath_inp', and 'fpath_out' columns to a specified maximum length and formats the 'epoch_srt' and 'epoch_end'
        columns as strings
        with a specific date-time format. The method then prints the formatted table to the logger.

        Parameters
        ----------
        no_print : bool, optional
            If True, the function does not print the table to the logger. Default is False.
        no_return : bool, optional
            If True, the function does not return the formatted table. Default is True.
        max_colwidth : int, optional
            The maximum length of the strings in the 'fraw', 'fpath_inp', and 'fpath_out' columns. Default is 33.

        Returns
        -------
        str or None
            The formatted table as a string if 'no_return' is False. Otherwise, None.
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
                The maximum length of the output string. Default is the value of the 'max_colwidth' parameter of the
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
                str_out = str_inp[:halflen] + ".." + str_inp[-halflen:]
                return str_out

        self.table_ok_cols_bool()

        form = dict()
        form["fraw"] = _shrink_str
        form["fpath_inp"] = _shrink_str
        form["fpath_out"] = _shrink_str

        form["epoch_srt"] = lambda t: t.strftime("%y-%m-%d %H:%M:%S")
        form["epoch_end"] = lambda t: t.strftime("%y-%m-%d %H:%M:%S")

        str_out = self.table.to_string(max_colwidth=max_colwidth + 1, formatters=form)
        # add +1 in max_colwidth for safety
        if not no_print:
            # print it in the logger (if silent , just return it)
            name = type(self).__name__
            logger.info("%s %s/%s\n%s", name, self.site_id, self.epoch_range, str_out)
        if no_return:
            return None
        else:
            return str_out

    def table_ok_cols_bool(self):
        """
        Converts the column of the table to boolean values.

        This method converts the specified column of the table to boolean values.
        The column is converted to True if the value is 'OK' and False otherwise.

        Wrapper for arocmn.is_ok()

        Returns
        -------
        None
        """
        self.table["ok_inp"] = self.table["ok_inp"].apply(arocmn.is_ok)
        self.table["ok_out"] = self.table["ok_out"].apply(arocmn.is_ok)

        return None

    def load_table_from_filelist(self, input_files, inp_regex=".*", reset_table=True):
        """
        Loads the table from a list of input files.

        This method takes a list of input files and uses it to update the current step's table.
        It sets the 'fpath_inp', 'fname', and 'ok_inp' columns of the table based on the input files.
        If 'reset_table' is True, it resets the current table before loading the new data.

        Parameters
        ----------
        input_files : list
            The list of input files to be loaded into the table.
            The input can be:
            * a python list
            * a text file path containing a list of files
            * a tuple containing several text files path
            * a directory path.
        inp_regex : str, optional
            The regular expression used to filter the input files. Default is ".*" which matches any file.
        reset_table : bool, optional
            If True, the current table is reset before loading the new data. Default is True.

        Returns
        -------
        list
            The list of input files that were loaded into the table.
        """
        if reset_table:
            self._init_table(init_epoch=False)

        flist = arocmn.files_input_manage(input_files, inp_regex)

        self.table["fpath_inp"] = flist
        self.table["fname"] = self.table["fpath_inp"].apply(os.path.basename)
        self.table["ok_inp"] = self.table["fpath_inp"].apply(os.path.isfile)

        return flist

    def load_table_from_prev_step_table(self, input_table, reset_table=True):
        """
        Loads the table from the previous step's table.

        This method takes the table from the previous step in the processing chain and uses it to update the current
        step's table.
        It copies the 'fpath_out', 'size_out', 'fname', 'site', 'epoch_srt', 'epoch_end', and 'ok_inp'
        columns from the input table to the current table.
        If 'reset_table' is True, it resets the current table before loading the new data.

        Parameters
        ----------
        input_table : pandas.DataFrame
            The table from the previous step in the processing chain. It should contain 'fpath_out', 'size_out',
            'fname', 'site', 'epoch_srt', 'epoch_end', and 'ok_inp' columns.
        reset_table : bool, optional
            If True, the current table is reset before loading the new data. Default is True.

        Returns
        -------
        None
        """
        if reset_table:
            self._init_table(init_epoch=False)

        self.table["fpath_inp"] = input_table["fpath_out"].values
        self.table["size_inp"] = input_table["size_out"].values
        self.table["fname"] = self.table["fpath_inp"].apply(os.path.basename)
        self.table["site"] = input_table["site"].values
        self.table["epoch_srt"] = input_table["epoch_srt"].values
        self.table["epoch_end"] = input_table["epoch_end"].values
        self.table["ok_inp"] = self.table["fpath_inp"].apply(os.path.isfile)

        return None

    def guess_local_rnx(self):
        """
        For a given site name and date in a table, guess the potential local RINEX files
        and write it as 'fpath_out' value in the table
        """

        #### to do: split it as a in_row fct

        local_paths_list = []

        ### no epoch at all, you are surely in convert mode
        if pd.isna(self.table["epoch_srt"]).all():
            logger.debug(
                "unable to get the epochs to generate local RINEX paths (normal in epoch-blind convert mode)"
            )
            return []

        ### some epochs are here, this is weirder and should not happen, we raise a warning
        if pd.isna(self.table["epoch_srt"]).any():
            logger.debug(
                "unable to get the epochs to generate local RINEX paths (something went wrong)"
            )
            return []

        for iepoch, epoch in self.table["epoch_srt"].items():
            # guess the potential local files
            local_dir_use = str(self.out_dir)
            # local_fname_use = str(self.inp_structure)

            epo_dt_srt = epoch.to_pydatetime()
            epo_dt_end = self.table.loc[iepoch, "epoch_end"].to_pydatetime()
            prd_str = rinexmod.rinexfile.file_period_from_timedelta(
                epo_dt_srt, epo_dt_end
            )[0]

            local_fname_use = conv.statname_dt2rinexname_long(
                self.site_id9,
                epoch,
                country="XXX",
                data_source="R",  ### always will be with autorino
                file_period=prd_str,
                data_freq=self.session["data_frequency"],
                data_type="MO",
                format_compression="crx.gz",
                preset_type=None,
            )

            local_path_use0 = os.path.join(local_dir_use, local_fname_use)

            local_path_use = self.translate_path(local_path_use0, epoch)

            local_fname_use = os.path.basename(local_path_use)

            local_paths_list.append(local_path_use)

            # iepoch = self.table[self.table['epoch_srt'] == epoch].index

            # self.table.loc[iepoch, 'fname'] = local_fname_use
            self.table.loc[iepoch, "fpath_out"] = local_path_use
            logger.debug("local RINEX file guessed: %s", local_path_use)

        logger.info("nbr local RINEX files guessed: %s", len(local_paths_list))

        return local_paths_list

    def check_local_files(self):
        """
        Checks the existence of the local files and updates the corresponding
        booleans in the 'ok_out' column of the table.

        This method iterates over each row in the table. For each row, it checks if the local file specified in
        the 'fpath_out' entry exists and is not empty.
        If the file exists and is not empty, the method sets the 'ok_out' entry for the file in the table to True and
        updates the 'size_out' entry with the size of the file.
        If the file does not exist or is empty, the method sets the 'ok_out' entry for the file in the table to False.
        The method returns a list of the paths of the existing and non-empty local files.

        Returns
        -------
        list
            The list of paths of the existing and non-empty local files.
        """
        local_files_list = []
        for irow, row in self.table.iterrows():
            local_file = row["fpath_out"]
            if (
                type(local_file) is float
            ):  ### if not initialized, value is NaN (and then a float)
                self.table.loc[irow, "ok_out"] = False
            else:
                if os.path.exists(local_file) and os.path.getsize(local_file) > 0:
                    self.table.loc[irow, "ok_out"] = True
                    self.table.loc[irow, "size_out"] = os.path.getsize(local_file)
                    local_files_list.append(local_file)
                else:
                    self.table.loc[irow, "ok_out"] = False

        return local_files_list

    def invalidate_small_local_files(self, threshold=0.80):
        """
        Invalidates local files that are smaller than a certain threshold.

        This method checks if the size of each local file is smaller than the threshold times
        the median size of all local files.
        If a file is smaller, the method sets the 'ok_out' entry for the file in the table to False,
        indicating that the file is invalid and needs to be redownloaded.
        The method returns a list of the paths of the invalidated files.

        Note: The 'check_local_files' method must be called before this method to ensure that
        the 'size_out' and 'ok_out' entries in the table are up-to-date.

        Parameters
        ----------
        threshold : float, optional
            The threshold for the file size, as a fraction of the median file size. Default is 0.80.

        Returns
        -------
        list
            The list of paths of the invalidated files.
        """

        if not self.table["size_out"].isna().all():
            med = self.table["size_out"].median(skipna=True)
            valid_bool = threshold * med < self.table["size_out"]
            self.table.loc[:, "ok_out"] = valid_bool
            invalid_local_files_list = list(self.table.loc[valid_bool, "fpath_out"])
        else:
            invalid_local_files_list = []

        return invalid_local_files_list

    def decompress(self, table_col="fpath_inp", table_ok_col="ok_inp"):
        """
        decompress the potential compressed files in the ``table_col`` column
        and its corresponding ``table_ok_col`` boolean column
        (usually ``fpath_inp`` and ``ok_inp``)

        It will uncompress the file if it is a
        (gzip+)Hatanaka-compressed RINEX, or a generic-compressed file
        (gzip only for the moment)

        It will create a new column ``fpath_ori`` (for original)
        to keep the trace of the original file

        Returns
        -------
        files_decmp_list
            the DEcompressed files i.e. the one which are temporary and must be removed
        files_uncmp_list
            the UNcompressed files i.e. ALL the usables ones

        """
        files_decmp_list = (
            []
        )  #### the DEcompressed files i.e. the one which are temporary and must be removed
        files_uncmp_list = []  #### the UNcompressed files i.e. ALL the usables ones

        for irow, row in self.table.iterrows():
            file_decmp, bool_decmp = self.on_row_decompress(
                irow, table_col=table_col, table_ok_col=table_ok_col
            )

            files_uncmp_list.append(file_decmp)  ### all files are stored in this list
            if bool_decmp:
                files_decmp_list.append(
                    file_decmp
                )  ### only the DEcompressed files are stored in this list (to be rm later)

        return files_decmp_list, files_uncmp_list

    def decompress_table_batch(self, table_col="fpath_inp", table_ok_col="ok_inp"):
        """
        Decompresses the potential compressed files in the specified column of the table.

        This method checks if the files specified in the 'table_col' column of the table are compressed.
        If they are, the method decompresses the files and updates the 'table_col' column with the paths of
        the decompressed files.
        It also updates the 'ok_inp' column with the existence of the decompressed files and the 'fname'
        column with the basenames of the decompressed files.
        If the files are not compressed or the 'ok_inp' column is False, the method does nothing.
        The method processes a complete table at once, which is faster than row-iterative decompression done by
        `decompress`.

        Parameters
        ----------
        table_col : str, optional
            The column in the table where the paths of the files are stored. Default is 'fpath_inp'.
        table_ok_col : str, optional
            The column in the table where the boolean indicating the existence of the files is stored.
            Default is 'ok_inp'.

        Returns
        -------
        list
            The list of paths of the decompressed files.
        """
        bool_comp = self.table[table_col].apply(arocmn.is_compressed)
        bool_ok = self.table[table_ok_col]
        bool_wrk = np.logical_and(bool_comp, bool_ok)
        idx_comp = self.table.loc[bool_wrk].index

        self.table.loc[idx_comp, "fpath_ori"] = self.table.loc[idx_comp, table_col]
        if hasattr(self, "tmp_dir_unzipped"):
            tmp_dir = self.tmp_dir_unzipped
        else:
            tmp_dir = self.tmp_dir
        files_decmp_list = self.table.loc[idx_comp, table_col].apply(
            arocmn.decompress_file, args=(tmp_dir,)
        )

        self.table.loc[idx_comp, table_col] = files_decmp_list
        self.table.loc[idx_comp, "ok_inp"] = self.table.loc[idx_comp, table_col].apply(
            os.path.isfile
        )
        self.table.loc[idx_comp, "fname"] = self.table.loc[idx_comp, table_col].apply(
            os.path.basename
        )

        return files_decmp_list

    def on_row_decompress(
        self, irow, out_dir=None, table_col="fpath_inp", table_ok_col="ok_inp"
    ):
        """
        "on row" method

        Decompresses the file specified in the 'table_col' entry of a given row in the table.

        This method checks if the file specified in the 'table_col' entry of the given row is compressed.
        If it is, the method decompresses the file and updates the 'table_col' entry with the path
        of the decompressed file.
        It also updates the 'ok_inp' entry with the existence of the decompressed file and the 'fname'
        entry with the basename of the decompressed file.
        If the file is not compressed or the 'ok_inp' entry is False, the method does nothing.

        Parameters
        ----------
        irow : int
            The index of the row in the table.
        out_dir : str, optional
            The output directory where the decompressed file will be stored. If not provided, the method
             uses the 'tmp_dir_unzipped' attribute if it exists, otherwise it uses the 'tmp_dir' attribute.
        table_col : str, optional
            The column in the table where the path of the file is stored. Default is 'fpath_inp'.
        table_ok_col : str, optional
            The column in the table where the boolean indicating the existence of the file is stored.
            Default is 'ok_inp'.

        Returns
        -------
        str, bool
            The path of the decompressed file and a boolean indicating whether the file was decompressed.
        """
        if not self.table.loc[irow, "ok_inp"]:
            # logger.warning(
            #    "action on row skipped (input disabled): %s",
            #    self.table.loc[irow, "fname"],
            # )
            # for decompress the warning message is not necessary and spams the log
            # (most of the files are not compressed in fact)
            file_decomp_out = None
            bool_decomp_out = False

            return file_decomp_out, bool_decomp_out

        # definition of the output directory (after the action)
        if out_dir:
            out_dir_use = out_dir
        elif hasattr(self, "tmp_dir_unzipped"):
            out_dir_use = self.tmp_dir_unzipped
        else:
            out_dir_use = self.tmp_dir

        bool_comp = arocmn.is_compressed(self.table.loc[irow, table_col])
        bool_ok = self.table.loc[irow, table_ok_col]
        bool_wrk = np.logical_and(bool_comp, bool_ok)

        if bool_wrk:
            if (
                "fpath_ori" not in self.table.columns
            ):  ## a 'fpath_ori' column must be created first
                self.table["fpath_ori"] = [None] * len(self.table)

            self.table.loc[irow, "fpath_ori"] = self.table.loc[irow, table_col]

            file_decomp_out, bool_decomp_out = arocmn.decompress_file(
                self.table.loc[irow, table_col], out_dir_use
            )
            self.table.loc[irow, table_col] = file_decomp_out
            self.table.loc[irow, "ok_inp"] = os.path.isfile(
                self.table.loc[irow, table_col]
            )
            self.table.loc[irow, "fname"] = os.path.basename(
                self.table.loc[irow, table_col]
            )

        else:
            file_decomp_out = None
            bool_decomp_out = False

        return file_decomp_out, bool_decomp_out

    def remove_tmp_files(self):
        """
        Removes the temporary files which have been stored in the two lists
        self.tmp_rnx_files and self.tmp_decmp_files.

        This method iterates over the lists of temporary RINEX and decompressed files.
        If a file exists and is not an original file, it is removed and its path is removed from the list.
        If a file does not exist or is an original file, its path is kept in the list for future reference.

        Note: This method modifies the 'tmp_rnx_files' and 'tmp_decmp_files' attributes of the object.

        See Also clean_tmp_dirs(), which clean all the temporary files based on their creation date

        Returns
        -------
        None
        """
        # TEMP RINEX Files
        tmp_rnx_files_new = []
        for f in self.tmp_rnx_files:
            if f and os.path.isfile(f):
                logger.debug("remove tmp converted RINEX file: %s", f)
                os.remove(f)
            else:
                tmp_rnx_files_new.append(f)
        self.tmp_rnx_files = tmp_rnx_files_new

        # TEMP decompressed Files
        tmp_decmp_files_new = []
        for f in self.tmp_decmp_files:
            # we also test if the file is not an original one!
            if "fpath_ori" not in self.table.columns:
                logger.warning(
                    "file has been uncompressed, but no 'fpath_ori' field in table, we keep it for security: %s",
                    f,
                )
                tmp_decmp_files_new.append(f)
                continue

            is_original = self.table["fpath_ori"].isin([f]).any()

            if f and os.path.isfile(f) and is_original:
                logger.warning(
                    "uncompressed file is also an original one, we keep it for security: %s",
                    f,
                )
                tmp_decmp_files_new.append(f)
                continue
            elif f and os.path.isfile(f) and not is_original:
                logger.debug("remove tmp decompress RINEX file: %s", f)
                os.remove(f)
            else:
                pass

        self.tmp_decmp_files = tmp_decmp_files_new

    #  ______ _ _ _              _        _     _
    # |  ____(_) | |            | |      | |   | |
    # | |__   _| | |_ ___ _ __  | |_ __ _| |__ | | ___
    # |  __| | | | __/ _ \ '__| | __/ _` | '_ \| |/ _ \
    # | |    | | | ||  __/ |    | || (_| | |_) | |  __/
    # |_|    |_|_|\__\___|_|     \__\__,_|_.__/|_|\___|

    def filter_bad_keywords(self, keywords_path_excl):
        """
        Filters a list of raw files if the full path contains certain keywords.

        This method checks if the full path of the raw files contains any of the provided keywords.
        If a keyword is found in the full path of a raw file, the file is filtered out.
        The method modifies the 'ok_inp' column of the object's table to reflect the filtering.
        The method returns a list of filtered raw files.

        Parameters
        ----------
        keywords_path_excl : list
            The list of keywords to filter the raw files.
            For example, if keywords_path_excl is ['badword1', 'badword2'],
            any file whose full path contains either 'badword1' or 'badword2' will be filtered out.

        Returns
        -------
        list
            The list of filtered raw files.
        """
        flist_out = []
        ok_inp_bool_stk = []
        nfil = 0
        for irow, row in self.table.iterrows():
            f = row["fname"]
            boolbad = utils.patterns_in_string_checker(f, *keywords_path_excl)
            if boolbad:
                self.table.iloc[irow, "ok_inp"] = False
                logger.debug("file filtered, contains an excluded keyword: %s", f)
                nfil += 1
            else:
                if not row.ok_inp:  # ok_inp is already false
                    ok_inp_bool_stk.append(False)
                else:
                    ok_inp_bool_stk.append(True)
                    flist_out.append(f)

        # final replace of ok init
        self.table["ok_inp"] = ok_inp_bool_stk

        logger.info("%6i files filtered, their paths contain bad keywords", nfil)
        return flist_out

    def filter_year_min_max(self, year_min=1980, year_max=2099, year_in_inp_path=None):
        """
        Filters a list of raw files based on their year range.

        This method checks if the year in the file path is within a specified range.
        The year is determined either by its position in the absolute path (if provided) or by a regex search.
        The method modifies the 'ok_inp' column of the object's table to reflect the filtering.
        The method returns a list of filtered raw files.

        Parameters
        ----------
        year_min : int, optional
            The minimum year for the range. Default is 1980.
        year_max : int, optional
            The maximum year for the range. Default is 2099.
        year_in_inp_path : int, optional
            The position of the year in the absolute path. If not provided, a regex search is performed.
            For example, if the absolute path is:
            /home/user/input_data/raw/2011/176/PSA1201106250000a.T00
            year_in_inp_path is 4

        Returns
        -------
        list
            The list of filtered raw files.
        """

        def _year_detect(fpath_inp, year_in_inp_path=None):
            """
            Detects the year in the file path.

            This function checks if a year_in_inp_path is provided.
            If it is, it gets the year from the specified position in the file path.
            If a year_in_inp_path is not provided, it performs a regex search to find the year.
            If the year cannot be found, it logs a warning and returns NaN.

            Parameters
            ----------
            fpath_inp : str
                The input file path.
            year_in_inp_path : int, optional
                The position of the year in the absolute path.

            Returns
            -------
            int or NaN
                The detected year or NaN if the year cannot be found.
            """
            try:
                if year_in_inp_path:
                    year_folder = int(fpath_inp.split("/")[year_in_inp_path])
                else:
                    rgx = re.search(r"/(19|20)[0-9]{2}/", fpath_inp)
                    year_folder = int(rgx.group()[1:-1])
                return year_folder
            except Exception:
                logger.warning("unable to get the year in path: %s", fpath_inp)
                return np.nan

        years = self.table["fraw"].apply(_year_detect, args=(year_in_inp_path,))

        bool_out_range = (years < year_min) | (years > year_max)
        bool_in_range = np.logical_not(bool_out_range)

        ok_inp_bool_stk = bool_in_range & self.table["ok_inp"]
        nfil_total = sum(bool_out_range)
        nfil_spec = sum(np.logical_and(bool_out_range, self.table["ok_inp"]))

        self.table["ok_inp"] = ok_inp_bool_stk

        flist_out = list(self.table.loc[self.table["ok_inp"], "fraw"])

        logger.info(
            "%6i/%6i files filtered (total/specific) not in the year min/max range (%4i/%4i)",
            nfil_total,
            nfil_spec,
            year_min,
            year_max,
        )

        return flist_out

    def filter_filelist(self, filelist_exclu_inp, message_manu_exclu=False):
        """
        Filters a list of raw files based on their presence in a provided exclusion list.

        This method checks if the raw files are present in the provided exclusion list.
        If a raw file is present in the exclusion list, it is filtered out.
        The method modifies the 'ok_inp' column of the object's table to reflect the filtering.
        The method returns a list of filtered raw files.

        Parameters
        ----------
        filelist_exclu_inp : str or list
            The exclusion list. It can be a string representing a path to a text file containing the exclusion list,
            or a list of strings representing the exclusion list.
        message_manu_exclu : bool, optional
            If True, a debug message is logged for each file that is manually filtered in the exclusion list.

        Returns
        -------
        list
            The list of filtered raw files.
        """
        flist_exclu = arocmn.files_input_manage(filelist_exclu_inp)

        flist_out = []
        ok_inp_bool_stk = []

        nfil = 0
        for irow, row in self.table.iterrows():
            f = row.fraw
            if f in flist_exclu:
                nfil += 1
                ok_inp_bool_stk.append(False)
                if not message_manu_exclu:
                    logger.debug(
                        "file filtered, was OK during a previous run (legacy simple list): %s",
                        f,
                    )
                else:
                    logger.debug("file filtered manually in the exclusion list: %s", f)
            else:
                if not row.ok_inp:  # ok_inp is already false
                    ok_inp_bool_stk.append(False)
                else:
                    ok_inp_bool_stk.append(True)
                    flist_out.append(f)

        if not message_manu_exclu:
            logger.info(
                "%6i files filtered, were OK during a previous run (legacy simple OK list)",
                nfil,
            )
        else:
            logger.info("%6i files manually filtered in the exclusion list,", nfil)

        # final replace of ok init
        self.table["ok_inp"] = ok_inp_bool_stk

        return flist_out

    def filter_ok_out(self):
        """
        Filters the raw files based on the 'ok_out' boolean column of the object's table.

        This method checks if the raw files have a positive 'ok_out' boolean (i.e., the converted file already exists).
        It modifies the 'ok_inp' boolean column of the object's table i.e. the step action must be done (True)
        or not (False) and returns the filtered raw files in a list.

        Returns
        -------
        list
            The list of filtered raw files.
        """

        def _not_impl(ok_inp, ok_out):
            """
            Implements the negation of an implication logic operation.

            This function takes two boolean inputs and returns the result of the operation
            "NOT(ok_inp => ok_out)" i.e. "ok_inp AND NOT(ok_out)".
            This operation is equivalent to the negation of an implication,
            as shown in the truth table below:

            ok_inp ok_out result
            0      0      0
            1      0      1
            0      1      0
            1      1      0

            Parameters
            ----------
            ok_inp : bool
                The first boolean input to the logic operation.
            ok_out : bool
                The second boolean input to the logic operation.

            Returns
            -------
            bool
                The result of the logic operation "ok_inp AND NOT(ok_out)".
            """
            res = np.logical_and(ok_inp, np.logical_not(ok_out))
            return res

        ok_inp_new = _not_impl(self.table["ok_inp"].values, self.table["ok_out"].values)

        flist_out = list(self.table["fpath_inp"][ok_inp_new])

        self.table["ok_inp"] = ok_inp_new

        return flist_out

    def filter_previous_tables_test_delme(self, df_prev_tab):
        """
        Filter a list of raw files if they are present in previous
        conversion tables stored as log

        modify the boolean "ok_inp" of the object's table
        returns the filtered raw files in a list
        """

        col_ok_names = ["ok_inp", "ok_out"]

        # previous files when everthing was ok
        prev_bool_ok = df_prev_tab[col_ok_names].apply(np.logical_and.reduce, axis=1)

        prev_files_ok = df_prev_tab[prev_bool_ok].fraw

        # current files which have been already OK and which have already
        # ok_inp == False
        # here the boolean value are inverted compared to the table:
        # True = skip me / False = keep me
        # a logical not inverts everything at the end
        curr_files_ok_prev = self.table["fraw"].isin(prev_files_ok)
        curr_files_off_already = np.logical_not(self.table["ok_inp"])

        curr_files_skip = np.logical_or(curr_files_ok_prev, curr_files_off_already)

        self.table["ok_inp"] = np.logical_not(curr_files_skip)

        logger.info(
            "%6i files filtered, were OK during a previous run (table list)",
            curr_files_ok_prev.sum(),
        )

        flist_out = list(self.table["fraw", self.table["ok_inp"]])

        return flist_out

    def filter_previous_tables(self, df_prev_tab):
        """
        Filters the raw files based on their presence in previous conversion tables.

        This method checks if the raw files are present in previous conversion tables that are stored as logs.
        If a raw file is present in the previous conversion tables, it is filtered out.
        The method modifies the 'ok_inp' column of the object's table to reflect the filtering.
        The method returns a list of filtered raw files.

        Parameters
        ----------
        df_prev_tab : pandas.DataFrame
            The previous conversion tables stored as a DataFrame.

        Returns
        -------
        list
            The list of filtered raw files.
        """
        col_ok_names = ["ok_inp", "ok_out"]

        # previous files when everything was ok
        prev_bool_ok = df_prev_tab[col_ok_names].apply(np.logical_and.reduce, axis=1)
        prev_files_ok = df_prev_tab.loc[prev_bool_ok, "fpath_inp"]

        # current files which have been already OK and which have already
        # ok_inp == False
        # here the boolean value are inverted compared to the table:
        # True = skip me / False = keep me
        # a logical not inverts everything at the end
        curr_files_ok_prev = self.table["fpath_inp"].isin(prev_files_ok)
        curr_files_off_already = np.logical_not(self.table["ok_inp"])

        curr_files_skip = np.logical_or(curr_files_ok_prev, curr_files_off_already)

        self.table["ok_inp"] = np.logical_not(curr_files_skip)
        self.table["ok_out"] = curr_files_ok_prev

        logger.info(
            "%6i files filtered, were OK during a previous run (table list)",
            curr_files_ok_prev.sum(),
        )

        flist_out = list(self.table.loc[self.table["ok_inp"], "fpath_inp"])

        return flist_out

    def filter_purge(self, col="ok_inp", inplace=False):
        """
        Filters the table based on the values in a specified column.

        This method removes all rows in the table where the value in the specified column is False.
        The method can either return a new DataFrame with the filtered data or modify the existing DataFrame in place.

        Parameters
        ----------
        col : str, optional
            The name of the column to use for filtering. The column should contain boolean values. Defaults to 'ok_inp'.
        inplace : bool, optional
            If True, the method will modify the existing DataFrame in place. If False, the method will return a new
            DataFrame with the filtered data. Defaults to False.

        Returns
        -------
        pandas.DataFrame or list
            If inplace is False, returns a new DataFrame with the filtered data. If inplace is True, returns a list of
            values in the specified column after filtering.
        """
        if len(self.table) == 0:
            logger.warning("the table is empty, unable to purge it")
            out = pd.DataFrame([])
        elif inplace:
            self.table = self.table[self.table[col]]
            out = list(self.table[col])
        else:
            out = self.table[self.table[col]]
        return out

    #               _   _
    #     /\       | | (_)
    #    /  \   ___| |_ _  ___  _ __  ___    ___  _ __    _ __ _____      _____
    #   / /\ \ / __| __| |/ _ \| '_ \/ __|  / _ \| '_ \  | '__/ _ \ \ /\ / / __|
    #  / ____ \ (__| |_| | (_) | | | \__ \ | (_) | | | | | | | (_) \ V  V /\__ \
    # /_/    \_\___|\__|_|\___/|_| |_|___/  \___/|_| |_| |_|  \___/ \_/\_/ |___/
    #

    def on_row_rinexmod(
        self, irow, out_dir=None, table_col="fpath_out", rinexmod_options=None
    ):
        """
        "on row" method

        Applies the rinexmod function to the 'table_col' entry of a specific row in the table.

        This method is applied on each row of the table. It checks if the 'ok_inp' column is True for the row.
        If it is, it applies the rinexmod function to the file specified in the 'table_col' column.
        The rinexmod function modifies the RINEX file according to the provided rinexmod_options.
        The modified file is then saved to the specified output directory.
        The method also updates the 'ok_out', 'table_col', and 'size_out' columns of the table for the row based on the
        success of the operation.

        Parameters
        ----------
        irow : int
            The index of the row in the table on which the method is applied.
        out_dir : str, optional
            The directory to which the modified file is saved. If not provided, the 'tmp_dir_rinexmoded' attribute of
            the object is used.
        table_col : str, optional
            The column in the table which contains the file path to be modified. Defaults to 'fpath_out'.
        rinexmod_options : dict, optional
            The options to be used by the rinexmod function. If not provided, default options are used.

        Returns
        -------
        str or None
            The path of the modified file if the operation is successful, None otherwise.
        """
        if not self.table.loc[irow, "ok_inp"]:
            logger.warning(
                "action on row skipped (input disabled): %s",
                self.table.loc[irow, "fname"],
            )
            return None

        # definition of the output directory (after the action)
        if out_dir:
            out_dir_use = out_dir
        elif hasattr(self, "tmp_dir_rinexmoded"):
            out_dir_use = self.tmp_dir_rinexmoded
        else:
            out_dir_use = self.tmp_dir

        # default options/arguments for rinexmod
        rinexmod_options_use = {
            # 'marker': 'XXXX', # forced in .convert()
            # 'sitelog': metadata, # forced in .convert()
            "compression": "gz",
            "longname": True,
            "force_rnx_load": True,
            "verbose": False,
            "tolerant_file_period": False,
            "full_history": True,
        }

        if (
            not rinexmod_options["sitelog"]
            and "station_info" in rinexmod_options.keys()
        ):
            rinexmod_options.pop("sitelog", None)

        # update options/arguments for rinexmod with inputs
        if rinexmod_options:
            debug_print_rinexmod_options = False
            if debug_print_rinexmod_options:
                logger.debug("input options for rinexmod: %s", rinexmod_options)
                logger.debug("default options for rinexmod: %s", rinexmod_options_use)
            rinexmod_options_use.update(rinexmod_options)
            if debug_print_rinexmod_options:
                logger.debug("final options for rinexmod: %s", rinexmod_options_use)

        frnx = self.table.loc[irow, table_col]

        try:
            frnxmod = rinexmod.rinexmod_api.rinexmod(
                frnx, out_dir_use, **rinexmod_options_use
            )
        except Exception as e:
            logger.error("something went wrong for %s", frnx)
            logger.error("Exception raised: %s", e)
            frnxmod = None

        if frnxmod:
            ### update table if things go well
            self.table.loc[irow, "ok_out"] = True
            self.table.loc[irow, table_col] = frnxmod
            self.table.loc[irow, "size_out"] = os.path.getsize(frnxmod)
            if (
                not self.table.loc[irow, "epoch_srt"]
                or not self.table.loc[irow, "epoch_end"]
            ):
                epo_srt_ok, epo_end_ok = rinexmod.rinexfile.dates_from_rinex_filename(
                    frnxmod
                )
                self.table.loc[irow, "epoch_srt"] = epo_srt_ok
                self.table.loc[irow, "epoch_end"] = epo_end_ok

            self.write_in_table_log(self.table.loc[irow])
        else:
            # ++ update table if things go wrong
            self.table.loc[irow, "ok_out"] = False
            self.write_in_table_log(self.table.loc[irow])
            # raise e

        return frnxmod

    def on_row_mv_final(self, irow, out_dir=None, table_col="fpath_out"):
        """
        "on row" method

        Moves the 'table_col' entry to a final destination for each row of the table.

        This method is applied on each row of the table. It checks if the 'ok_out' column is True for the row.
        If it is, it moves the file specified in the 'table_col' column to a final destination directory.
        The final destination directory is either provided as an argument or it defaults to the 'out_dir' attribute of
        the object.
        The method also updates the 'ok_out', 'table_col', and 'size_out' columns of the table for the row based on the
        success of the operation.

        Parameters
        ----------
        irow : int
            The index of the row in the table on which the method is applied.
        out_dir : str, optional
            The directory to which the file is moved. If not provided, the 'out_dir' attribute of the object is used.
        table_col : str, optional
            The column in the table which contains the file path to be moved. Defaults to 'fpath_out'.

        Returns
        -------
        str or None
            The final path of the moved file if the operation is successful, None otherwise.
        """
        if not self.table.loc[
            irow, "ok_out"
        ]:  ### for mv it's ok_out column the one to check!!!!
            logger.warning(
                "action on row skipped (input disabled): %s",
                self.table.loc[irow, "fname"],
            )
            return None

        # definition of the output directory (after the action)
        if out_dir:
            out_dir_use = out_dir
        else:
            out_dir_use = self.out_dir

        ### def output folders
        outdir_use = self.translate_path(
            out_dir_use, epoch_inp=self.table.loc[irow, "epoch_srt"]
        )

        frnx_to_mv = self.table.loc[irow, table_col]

        try:
            ### do the move
            utils.create_dir(outdir_use)
            frnxfin = shutil.copy2(frnx_to_mv, outdir_use)
            logger.debug("file moved to final destination: %s", frnxfin)
        except Exception as e:
            logger.error("something went wrong for %s", frnx_to_mv)
            logger.error("Exception raised: %s", e)
            frnxfin = None

        if frnxfin:
            ### update table if things go well
            self.table.loc[irow, "ok_out"] = True
            self.table.loc[irow, table_col] = frnxfin
            self.table.loc[irow, "size_out"] = os.path.getsize(frnxfin)
        else:
            ### update table if things go wrong
            self.table.loc[irow, "ok_out"] = False
            self.write_in_table_log(self.table.loc[irow])
            # raise e

        return frnxfin
