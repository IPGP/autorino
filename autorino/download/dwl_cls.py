#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import shutil

import numpy as np
import pandas as pd

import autorino.common as arocmn
import autorino.download as arodwl
import warnings


# +++ Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger("autorino")
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])

# pd.options.mode.chained_assignment = "warn"
warnings.simplefilter("ignore", category=RuntimeWarning)

BOLD_SRT = "\033[1m"
BOLD_END = "\033[0m"


class DownloadGnss(arocmn.StepGnss):
    """
    A class to handle the downloading of GNSS data.

    Inherits from
    ----------
    arocmn.StepGnss

    Parameters
    ----------
    out_dir : str
        The output directory where the downloaded files will be stored.
    tmp_dir : str
        The temporary directory used during the download process.
    log_dir : str
        The directory where log files will be stored.
    epoch_range : EpochRange
        The range of epochs for which data will be downloaded.
    access : dict
        A dictionary containing access information such as protocol, hostname, login, and password.
    site : dict, optional
        The site information. Default is None.
    session : dict, optional
        The session information. Default is None.
    options : dict, optional
        Additional options for the download process. Default is None.
    metadata : str or list, optional
        The metadata to be included in the converted RINEX files. Possible inputs are:
         * list of string (sitelog file paths),
         * single string (single sitelog file path)
         * single string (directory containing the sitelogs)
         * list of MetaData objects
         * single MetaData object.
         Defaults to None.
    """

    def __init__(
        self,
        out_dir,
        tmp_dir,
        log_dir,
        inp_dir,
        inp_file_regex,
        epoch_range,
        access,
        site=None,
        session=None,
        options=None,
        metadata=None,
    ):
        """
        Initialize the DownloadGnss object.

        Parameters
        ----------
        out_dir : str
            The output directory where the downloaded files will be stored.
        tmp_dir : str
            The temporary directory used during the download process.
        log_dir : str
            The directory where log files will be stored.
        epoch_range : EpochRange
            The range of epochs for which data will be downloaded.
        access : dict
            A dictionary containing access information such as protocol, hostname, login, and password.
        site : dict, optional
            The site information. Default is None.
        session : dict, optional
            The session information. Default is None.
        options : dict, optional
            Additional options for the download process. Default is None.
        metadata : str or list, optional
            The metadata to be included in the converted RINEX files. Possible inputs are:
             * list of string (sitelog file paths),
             * single string (single sitelog file path)
             * single string (directory containing the sitelogs)
             * list of MetaData objects
             * single MetaData object.
             Defaults to None.
        """
        super().__init__(
            out_dir=out_dir,
            tmp_dir=tmp_dir,
            log_dir=log_dir,
            inp_dir=inp_dir,
            inp_file_regex=inp_file_regex,
            epoch_range=epoch_range,
            site=site,
            session=session,
            options=options,
            metadata=metadata,
        )

        # specific to the DownloadGnss class
        self.access = access

        # initialize the ftp object
        self.ftp_obj = None

    # legacy properties, specific to the DownloadGnss class
    #### They become more or less useless since the implementation of self.inp_file_regex (2025-01)
    @property
    def inp_dirname(self):
        return os.path.dirname(self.inp_dir)

    @property
    def inp_basename(self):
        return os.path.basename(self.inp_dir)

    def guess_remot_raw(self):
        """
        Guess the paths and name of the remote files based on the
        Session and EpochRange attributes of the DownloadGnss

        see also method ``guess_local_raw()``
        """

        if not self.inp_file_regex:
            logger.warning(
                "generic filename empty for %s, the guessed remote filepaths will be wrong",
                self.session,
            )

        hostname_use = self.access["hostname"]

        rmot_paths_list = []

        # for epoch in self.epoch_range.eporng_list():  ### go for irow ! ### IMPROVE ME !!!

        for irow, row in self.table.iterrows():
            # epoch = row["epoch_srt"]

            ### guess the potential remote files
            rmot_dir_use = str(self.inp_dir)
            rmot_fname_use = str(self.inp_file_regex)

            rmot_path_use = arodwl.join_url(
                self.access["protocol"], hostname_use, rmot_dir_use, rmot_fname_use
            )

            rmot_path_use = self.translate_path(rmot_path_use, row["epoch_srt"], make_dir=False)

            rmot_fname_use = os.path.basename(rmot_path_use)

            rmot_paths_list.append(rmot_path_use)

            # iepoch = self.table[self.table["epoch_srt"] == epoch].index[0]

            self.table.loc[irow, "fname"] = rmot_fname_use
            self.table.loc[irow, "fpath_inp"] = rmot_path_use
            logger.debug("remote file guessed: %s", rmot_path_use)

        # for guess, all input files are considered as ok a priori
        self.table["ok_inp"] = True

        rmot_paths_list = sorted(list(set(rmot_paths_list)))

        logger.info("nbr remote files guessed: %s", len(rmot_paths_list))

        return rmot_paths_list

    def guess_local_raw(self):
        """
        Guess the paths and name of the local raw files based on the
        EpochRange and `inp_file_regex` attributes of the DownloadGnss object

        see also method ``guess_remot_raw()``,
        """

        local_paths_list = []

        # for epoch in self.epoch_range.eporng_list():  # go for irow ! ### IMPROVE ME !!!

        for irow, row in self.table.iterrows():
            # epoch = row["epoch_srt"]

            # guess the potential local files
            local_dir_use = str(self.out_dir)
            local_fname_use = str(self.inp_file_regex)
            local_path_use = os.path.join(local_dir_use, local_fname_use)

            local_path_use = self.translate_path(local_path_use, row["epoch_srt"], make_dir=False)

            local_fname_use = os.path.basename(local_path_use)

            local_paths_list.append(local_path_use)

            # iepoch = self.table[self.table["epoch_srt"] == epoch].index

            self.table.loc[irow, "fname"] = local_fname_use
            self.table.loc[irow, "fpath_out"] = local_path_use
            logger.debug("local file guessed: %s", local_path_use)

        logger.info("nbr local raw files guessed: %s", len(local_paths_list))

        return local_paths_list

    def guess_remote_dirs(self):
        """
        this method is specific for ask_remote_raw
        guessing the directories is different from guessing the files:
        * no hostname
        * no filename (obviously)
        """
        rmot_dir_list = []
        for irow, row in self.table.iterrows():
            epoch = self.table.loc[irow, "epoch_srt"]
            rmot_dir_use = str(self.inp_dirname)
            rmot_dir_use = self.translate_path(rmot_dir_use, epoch, make_dir=False)
            row["fpath_inp"] = rmot_dir_use
            row["note"] = "dir_guessed"
            self.table.iloc[irow] = row

            rmot_dir_list.append(rmot_dir_use)

        rmot_dir_list = sorted(list(set(rmot_dir_list)))
        return rmot_dir_list

    def ask_remote_raw(self):
        """
        Retrieve the list of remote files from the server.

        This method guesses the remote directories and then lists the files
        in those directories based on the protocol specified in the access
        information.

        Returns
        -------
        list
            A list of remote file paths.
        """

        # guess the remote directories
        self.guess_remote_dirs()

        rmot_fil_all_lis = []
        rmot_fil_epo_lis = []
        epo_lis = []

        if self.inp_file_regex:
            logger.debug(f"regex to filter remote files (aliases not translated yet): {self.inp_file_regex}")
        else:
            logger.debug("no filter regex will be applied to remote files")

        # step 1: iterate over the input table and list the remote files (table is updated in step 2)
        for irow, row in self.table.iterrows():
            epoch = row["epoch_srt"]
            rmot_dir_use = row["fpath_inp"]

            if self.access["protocol"] == "http":
                logger.warning(
                    "HTTP protocol doesn't support well file listing. Nasty effects may occur."
                )
                rmot_fil_epo_bulk_lis = arodwl.list_remote_http(
                    self.access["hostname"], rmot_dir_use
                )
            elif self.access["protocol"] == "ftp":
                rmot_fil_epo_bulk_lis = arodwl.list_remote_ftp(
                    self.access["hostname"],
                    rmot_dir_use,
                    self.access["login"],
                    self.access["password"],
                    ftp_obj_inp=self.ftp_obj,
                )

            else:
                logger.error("wrong protocol. Only 'http' and 'ftp' are supported.")
                raise Exception

            rmot_fil_epo_bulk_lis = list(rmot_fil_epo_bulk_lis)

            ### match the right input structure, if a regex input is provided
            if self.inp_file_regex:
                rmot_fname_theo = re.compile(
                    self.translate_path(self.inp_file_regex, epoch, make_dir=False)
                )
                rmot_fil_epo_lis = [
                    f
                    for f in rmot_fil_epo_bulk_lis
                    if rmot_fname_theo.search(os.path.basename(f))
                ]
            else:
                rmot_fil_epo_lis = rmot_fil_epo_bulk_lis

            logger.debug(
                "%i remote files found on rec: %s",
                len(rmot_fil_epo_lis),
                rmot_fil_epo_lis,
            )
            if len(rmot_fil_epo_lis) != len(rmot_fil_epo_bulk_lis):
                logger.warning(
                    "%i files have been filtered out (non-matching regex)",
                    len(rmot_fil_epo_bulk_lis) - len(rmot_fil_epo_lis),
                )

            rmot_fil_all_lis = rmot_fil_all_lis + rmot_fil_epo_lis
            epo_lis = epo_lis + [epoch] * len(rmot_fil_epo_lis)

            # re add protocol: (urltambouille)
            rmot_fil_epo_lis = [
                arodwl.join_url(self.access["protocol"], "", "", f)
                for f in rmot_fil_epo_lis
            ]
            # legacy readd
            # rmot_fil_epo_lis = [
            #    self.access["protocol"] + "://" + f for f in rmot_fil_epo_lis
            # ]

            ## step 2: the table is updated with the files found
            new_rows_stk = []
            for rmot_fil in rmot_fil_epo_lis:
                new_row = row.copy()
                new_row["fname"] = os.path.basename(rmot_fil)
                new_row["fpath_inp"] = rmot_fil
                new_row["note"] = ""
                new_row["ok_inp"] = True
                new_rows_stk.append(new_row)

            self.table = pd.concat(
                [self.table, pd.DataFrame(new_rows_stk)], ignore_index=True
            )

        # step 3: remove the guessed directories
        self.table = self.table[self.table["note"] != "dir_guessed"]
        self.table.reset_index(drop=True, inplace=True)

        logger.info("nbr remote files found on rec: %s", len(rmot_fil_all_lis))
        return rmot_fil_all_lis

    def ask_local_raw(self):
        """
        Guess the paths and name of the local raw files based on the
        EpochRange and  table's fpath_inp basename i.e. the theoretical remote file name
        generated with `guess_remot_raw()`.

        see also method ``guess_remot_raw()``,
        """

        local_paths_list = []

        for irow, row in self.table.iterrows():
            epoch = row["epoch_srt"]

            # guess the potential local files
            local_dir_use = str(self.out_dir)
            local_fname_use = os.path.basename(row["fpath_inp"])
            local_path_use = os.path.join(local_dir_use, local_fname_use)
            local_path_use = self.translate_path(local_path_use, epoch, make_dir=False)

            local_paths_list.append(local_path_use)

            self.table.loc[irow, "fname"] = local_fname_use
            self.table.loc[irow, "fpath_out"] = local_path_use
            logger.debug("local file asked: %s", local_path_use)

        logger.info("nbr local raw files asked: %s", len(local_paths_list))

        return local_paths_list

    def ping_remote(self, ping_max_try=4, ping_timeout=20):
        """
        Ping the remote server to check if it is reachable.
        """
        count = 0
        ping_out = None
        while count < ping_max_try and not ping_out:
            ping_out = arodwl.ping(
                host=self.access["hostname"], ping_timeout=ping_timeout
            )
            count += 1
            if count > 1:
                logger.warning(
                    "attempt %i/%i to ping %s",
                    count,
                    ping_max_try,
                    self.access["hostname"],
                )

        if not ping_out:
            logger.error("Remote server %s is not reachable.", self.access["hostname"])
            self.exit_code = 7
        else:
            logger.info(
                "Remote server %s is reachable. (%d ms)",
                self.access["hostname"],
                int(ping_out * 10**3),
            )

        return ping_out

    def set_ftp_obj(self, timeout=15, max_try=4, sleep_time=5):
        """
        Create the FTP object for the FTP protocol.
        """
        self.ftp_obj = arodwl.ftp_create_obj(
            hostname_inp=self.access["hostname"],
            username=self.access["login"],
            password=self.access["password"],
            timeout=timeout,
            max_try=max_try,
            sleep_time=sleep_time,
        )

    def download(
        self,
        verbose=False,
        force=False,
        remote_find_method="ask",
        invalidate_small_local_files=True,
        timeout=60,
        max_try=4,
        sleep_time=5,
        ping_max_try=4,
        ping_timeout=20,
        ping_disable=False,
    ):
        """
        Frontend method to download files from a GNSS receiver

        Parameters
        ----------
        verbose : bool, optional
            If True, prints detailed information during the download process. Default is False.
        force : bool, optional
            If True, forces the download even if the files already exist locally. Default is False.
        remote_find_method : str, optional
            Method to find remote files.
            Can be 'ask' to list files from the server (for FTP only) or 'guess' to guess file paths.
            Default is 'ask'.
        invalidate_small_local_files : bool, optional
            If True, invalidates small local files to ensure they are re-downloaded. Default is True.
        timeout : int, optional
            Timeout in seconds for the download operations. Default is 60.
        max_try : int, optional
            Maximum number of retry attempts for the download operations. Default is 4.
        sleep_time : int, optional
            Sleep time in seconds between retry attempts. Default is 5.
        ping_max_try : int, optional
            Maximum number of retry attempts for pinging the remote server. Default is 4.
        ping_timeout : int, optional
            Timeout in seconds for pinging the remote server. Default is 20.
        ping_disable : bool, optional
            If True, skips the pinging of the remote server. Default is False.

        Returns
        -------
        None
        """
        self.set_logfile()
        logger.info(BOLD_SRT + ">>>>>> RAW files download" + BOLD_END)

        # Set up and clean temporary directories
        self.set_tmp_dirs()
        self.clean_tmp_dirs()

        # Check the remote find method, and switch to 'guess' if HTTP protocol is used
        if remote_find_method == "ask" and self.access["protocol"] == "http":
            logger.warning("HTTP protocol doesn't support file listing ('ask' method).")
            logger.warning("Switching to 'guess' remote find method.")
            remote_find_method = "guess"

        # Ping the remote server to check if it is reachable (unless ping_disable is True)
        ping_out = True if ping_disable else self.ping_remote(ping_max_try, ping_timeout)

        if not ping_out:
            # local raw are guessed anyway, to resume the next steps if download is not possible
            self.guess_local_raw()
            return None

        # Set up the DownloadGnss's FTP object if the protocol is FTP
        if self.access["protocol"] == "ftp":
            self.set_ftp_obj(timeout=timeout, max_try=max_try, sleep_time=sleep_time)

        # Guess remote raw file paths
        if remote_find_method == "guess":
            self.guess_remot_raw()
            self.guess_local_raw()
        # Ask remote raw file paths (works for FTP only!
        elif remote_find_method == "ask":
            self.ask_remote_raw()
            self.ask_local_raw()
        else:
            logger.error(
                "Wrong remote_find_method: %s ('ask' or 'guess' only are allowed)",
                remote_find_method,
            )
            raise Exception

        # Check local files and update table
        self.check_local_files()
        # be sure ok_xxx columns are booleans
        self.table_ok_cols_bool()
        if invalidate_small_local_files:
            self.invalidate_small_local_files()
        # switch ok_inp to False if the output files are already there
        self.filter_ok_out()

        # Force download if required
        if force:
            self.force(step_name="download")

        # Log the number of files to be downloaded and excluded
        n_ok_inp = (self.table["ok_inp"]).sum()
        n_not_ok_inp = np.logical_not(self.table["ok_inp"]).sum()
        n_tot_inp = len(self.table)

        logger.info(
            "%3i/%3i files will be downloaded, %3i/%3i files are excluded",
            n_ok_inp,
            n_tot_inp,
            n_not_ok_inp,
            n_tot_inp,
        )

        # Print the table if verbose is enabled
        if verbose:
            self.print_table()

        # Create a lockfile to ensure exclusive access during download
        lock = self.create_lockfile()

        ###############################
        # +++ DOWNLOAD CORE a.k.a FETCH
        lock.acquire()
        try:
            self.fetch_remote_files(
                force=force,  # force argument is now redudant, because ok_inp can be forced with .force() method
                timeout=timeout,
                max_try=max_try,
                sleep_time=sleep_time,
            )
        finally:
            lock.release()
            os.remove(lock.lock_file)
        ###############################

        # Print the table if verbose is enabled
        if verbose:
            self.print_table()

        # close the log file
        self.close_logfile()

        return None

    def fetch_remote_files(self, force=False, timeout=60, max_try=4, sleep_time=5):
        """
        will download locally the files which have been identified by
        the guess_remote_files method

        exploits the fname_remote column of the DownloadGnss.table
        attribute

        This `fetch_remote_files` method is for the download stricly speaking.
        Ìn operation, use the `download` method which does a broader
        preliminary actions.
        """
        download_files_list = []

        for irow, row in self.table.iterrows():
            file_dl_out = self.mono_fetch(
                irow,
                force=force,  # force argument is now redudant, because ok_inp can be forced with .force() method
                timeout=timeout,
                max_try=max_try,
                sleep_time=sleep_time,
            )
            if file_dl_out:
                download_files_list.append(file_dl_out)

        return download_files_list

    #               _   _                   _ _                           _ _    __                                 __
    #     /\       | | (_)                 ( | )                         ( | )  / /                                 \ \
    #    /  \   ___| |_ _  ___  _ __  ___   V V_ __ ___   ___  _ __   ___ V V  | | ___  _ __    _ __ _____      _____| |
    #   / /\ \ / __| __| |/ _ \| '_ \/ __|    | '_ ` _ \ / _ \| '_ \ / _ \     | |/ _ \| '_ \  | '__/ _ \ \ /\ / / __| |
    #  / ____ \ (__| |_| | (_) | | | \__ \    | | | | | | (_) | | | | (_) |    | | (_) | | | | | | | (_) \ V  V /\__ \ |
    # /_/    \_\___|\__|_|\___/|_| |_|___/    |_| |_| |_|\___/|_| |_|\___/     | |\___/|_| |_| |_|  \___/ \_/\_/ |___/ |
    #                                                                           \_\                                 /_/

    def mono_fetch(self, irow, force=False, timeout=60, max_try=4, sleep_time=5):

        if not self.mono_ok_check(irow, "fetch"):
            return None

        logger.info(">>>> fetch remote raw file: %s", self.table.loc[irow, "fname"])

        # ++++++ use the guessed local file as destination or the generic directory
        if not arocmn.is_ok(self.table.loc[irow, "fpath_out"]):
            # +++ the local file has not been guessed
            outdir_use = str(self.out_dir)
            outdir_use = self.translate_path(
                outdir_use, self.table.loc[irow, "epoch_srt"], make_dir=True
            )
        else:  # +++ the local file has been guessed before
            outdir_use = os.path.dirname(self.table.loc[irow, "fpath_out"])

        tmpdir_use = self.tmp_dir_downloaded

        # +++++ create the directory if it does not exist
        if not os.path.exists(outdir_use):
            os.makedirs(outdir_use)

        # +++++ download the file
        file_dl_tmp = None
        file_dl_out = None
        if not self.access["protocol"] in ("ftp", "http"):
            logger.critical("wrong protocol %s", self.access["protocol"])
            raise Exception
        elif self.access["protocol"] == "http":
            try:
                file_dl_tmp = arodwl.download_http(
                    url=self.table.loc[irow, "fpath_inp"],
                    output_dir=tmpdir_use,
                    timeout=timeout,
                    max_try=max_try,
                    sleep_time=sleep_time,
                )
                dl_ok = True
            except Exception as e:
                logger.error("HTTP download error: %s", str(e))
                dl_ok = False

        elif self.access["protocol"] == "ftp":
            try:
                file_dl_tmp = arodwl.download_ftp(
                    self.table.loc[irow, "fpath_inp"],
                    tmpdir_use,
                    username=self.access["login"],
                    password=self.access["password"],
                    timeout=timeout,
                    max_try=max_try,
                    sleep_time=sleep_time,
                    ftp_obj_inp=self.ftp_obj,
                )
                dl_ok = True
            except Exception as e:
                logger.error("FTP download error: %s", str(e))
                dl_ok = False

        else:  # ++ this case should never happen since there is a protocol test at the begining
            dl_ok = False
            pass

        # +++++ check the downloaded file size
        if dl_ok:
            dl_ok, _ = arodwl.check_file_size(file_dl_tmp)

        # +++++ store the results in the table
        if dl_ok:
            file_dl_out = shutil.copy(file_dl_tmp, outdir_use)
            self.table.loc[irow, "ok_out"] = True
            self.table.loc[irow, "fpath_out"] = file_dl_out
            os.remove(file_dl_tmp)
        else:
            self.table.loc[irow, "ok_out"] = False

        return file_dl_out
