#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ftplib
import os
import shutil
import numpy as np

import autorino.common as arocmn
import autorino.download as arodwl

#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger(__name__)
logger.setLevel(aroenv.aro_env_dict["general"]["log_level"])


import warnings

# pd.options.mode.chained_assignment = "warn"
warnings.simplefilter("ignore", category=RuntimeWarning)


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
    inp_dir_parent : str
        The parent directory of the input files.
    inp_structure : str
        The structure of the input files.
    site : str, optional
        The site identifier. Default is None.
    session : str, optional
        The session identifier. Default is None.
    options : dict, optional
        Additional options for the download process. Default is None.
    metadata : dict, optional
        Metadata associated with the download process. Default is None.
    """

    def __init__(
        self,
        out_dir,
        tmp_dir,
        log_dir,
        epoch_range,
        access,
        inp_dir_parent,
        inp_structure,
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
        inp_dir_parent : str
            The parent directory of the input files.
        inp_structure : str
            The structure of the input files.
        site : str, optional
            The site identifier. Default is None.
        session : str, optional
            The session identifier. Default is None.
        options : dict, optional
            Additional options for the download process. Default is None.
        metadata : dict, optional
            Metadata associated with the download process. Default is None.
        """
        super().__init__(
            out_dir,
            tmp_dir,
            log_dir,
            epoch_range,
            site=site,
            session=session,
            options=options,
            metadata=metadata,
        )

        self.access = access
        self.inp_dir_parent = inp_dir_parent
        self.inp_structure = inp_structure

    def guess_remote_raw(self):
        """
        Guess the paths and name of the remote files based on the
        Session and EpochRange attributes of the DownloadGnss

        see also method ``guess_local_raw()``
        """
        ### wrong but legacy docstring
        # see also method guess_local_raw(), a general method for all
        # StepGnss objects

        if not self.inp_structure:
            logger.warning(
                "generic filename empty for %s, the guessed remote filepaths will be wrong",
                self.session,
            )

        hostname_use = self.access["hostname"]

        rmot_paths_list = []

        for epoch in self.epoch_range.epoch_range_list():
            ### guess the potential remote files
            rmot_dir_use = str(self.inp_dir_parent)
            rmot_fname_use = str(self.inp_structure)

            rmot_path_use = arodwl.join_url(
                self.access["protocol"], hostname_use, rmot_dir_use, rmot_fname_use
            )

            rmot_path_use = self.translate_path(rmot_path_use, epoch, make_dir=False)

            rmot_fname_use = os.path.basename(rmot_path_use)

            rmot_paths_list.append(rmot_path_use)

            iepoch = self.table[self.table["epoch_srt"] == epoch].index[0]

            self.table.loc[iepoch, "fname"] = rmot_fname_use
            self.table.loc[iepoch, "fpath_inp"] = rmot_path_use
            logger.debug("remote file guessed: %s", rmot_path_use)

        rmot_paths_list = sorted(list(set(rmot_paths_list)))

        logger.info("nbr remote files guessed: %s", len(rmot_paths_list))

        return rmot_paths_list

    def guess_local_raw(self):
        """
        Guess the paths and name of the local raw files based on the
        EpochRange and `inp_structure` attributes of the DownloadGnss object

        see also method ``guess_remote_raw()``,
        """
        ### wrong but legacy docstring
        # If the object is not a DownloadGnss one,
        # You must provide as ``remote_fname_inp``, which is usually
        # a ``DownloadGnss.inp_structure`` attribute

        # see also method ``guess_remote_raw()``,
        # a specific method for DownloadGnss objects

        local_paths_list = []

        for epoch in self.epoch_range.epoch_range_list():
            # guess the potential local files
            local_dir_use = str(self.out_dir)
            local_fname_use = str(self.inp_structure)
            local_path_use = os.path.join(local_dir_use, local_fname_use)

            local_path_use = self.translate_path(local_path_use, epoch, make_dir=False)

            local_fname_use = os.path.basename(local_path_use)

            local_paths_list.append(local_path_use)

            iepoch = self.table[self.table["epoch_srt"] == epoch].index

            self.table.loc[iepoch, "fname"] = local_fname_use
            self.table.loc[iepoch, "fpath_out"] = local_path_use
            logger.debug("local file guessed: %s", local_path_use)

        logger.info("nbr local raw files guessed: %s", len(local_paths_list))

        return local_paths_list

    def _guess_remote_directories(self):
        """
        this method is specific for ask_remote_files
        guessing the directories is different than guessing the files:
        * no hostname
        * no filename (obviously)
        """
        rmot_dir_list = []
        for epoch in self.epoch_range.epoch_range_list():
            rmot_dir_use = str(self.inp_dir_parent)
            rmot_dir_use = self.translate_path(rmot_dir_use, epoch, make_dir=False)
            rmot_dir_list.append(rmot_dir_use)

        rmot_dir_list = sorted(list(set(rmot_dir_list)))

        return rmot_dir_list

    def ask_remote_files(self):
        rmot_dir_list = self._guess_remote_directories()
        rmot_files_list = []
        list_ = []
        for rmot_dir_use in rmot_dir_list:
            if self.access["protocol"] == "http":
                list_ = arodwl.list_remote_files_http(
                    self.access["hostname"], rmot_dir_use
                )
                rmot_files_list = rmot_files_list + list_
            elif self.access["protocol"] == "ftp":
                list_ = arodwl.list_remote_files_ftp(
                    self.access["hostname"],
                    rmot_dir_use,
                    self.access["login"],
                    self.access["password"],
                )
                rmot_files_list = rmot_files_list + list_
            else:
                logger.error("wrong protocol")

            logger.debug("remote files found on rec: %s", list_)

        logger.info("nbr remote files found on rec: %s", len(rmot_files_list))
        return rmot_files_list

    def fetch_remote_files(self, force_download=False):
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

            epoch = row["epoch_srt"]
            rmot_file = row["fpath_inp"]
            local_file = row["fpath_out"]

            ###### check if the file exists locally
            if row.ok_out == True and not force_download:
                logger.info(
                    "%s already exists locally, skip", os.path.basename(local_file)
                )
                continue

            ###### use the guessed local file as destination or the generic directory
            if not local_file:  #### the local file has not been guessed
                outdir_use = str(self.out_dir)
                outdir_use = self.translate_path(outdir_use, epoch, make_dir=True)
            else:  #### the local file has been guessed before
                outdir_use = os.path.dirname(local_file)

            tmpdir_use = self.tmp_dir_downloaded

            ###### create the directory if it does not exists
            if not os.path.exists(outdir_use):
                os.makedirs(outdir_use)

            ###### download the file
            file_dl_tmp = None
            file_dl_out = None
            if not self.access["protocol"] in ("ftp", "http"):
                logger.error("wrong protocol")
                raise Exception
            elif self.access["protocol"] == "http":
                try:
                    file_dl_tmp = arodwl.download_file_http(rmot_file, tmpdir_use)
                    file_dl_out = shutil.copy(file_dl_tmp, outdir_use)
                    dl_ok = True
                except Exception as e:
                    logger.error("HTTP download error: %s", str(e))
                    dl_ok = False

            elif self.access["protocol"] == "ftp":
                try:
                    file_dl_tmp = arodwl.download_file_ftp(
                        rmot_file,
                        tmpdir_use,
                        self.access["login"],
                        self.access["password"],
                    )
                    dl_ok = True
                    file_dl_out = shutil.copy(file_dl_tmp, outdir_use)
                except ftplib.error_perm as e:
                    logger.error("FTP download error: %s", str(e))
                    dl_ok = False

            else:  ### this case should never happen since there is a protocol test at the begining
                dl_ok = False
                pass

            ###### store the results in the table
            if dl_ok:
                download_files_list.append(file_dl_out)
                self.table.loc[irow, "ok_out"] = True
                self.table.loc[irow, "fpath_out"] = file_dl_out
                os.remove(file_dl_tmp)
            else:
                self.table.loc[irow, "ok_out"] = False

        return download_files_list

    def ping_remote(self):
        """
        Ping the remote server to check if it is reachable.
        """

        count = 0
        ping_out = None
        count_max = 4
        while count < count_max and not ping_out:
            ping_out = arodwl.ping(self.access["hostname"])
            count += 1
            if count > 1:
                logger.warning(
                    "attempt %i/%i to ping %s",
                    count,
                    count_max,
                    self.access["hostname"],
                )

        if not ping_out:
            logger.error("Remote server %s is not reachable.", self.access["hostname"])
        else:
            logger.info(
                "Remote server %s is reachable. (%f ms)",
                self.access["hostname"],
                ping_out * 10**3,
            )

        return ping_out

    def download(self, verbose=False, force=False):
        """
        frontend method to download files from a GNSS receiver
        """

        if self.options.get("force") or force:
            force_use = True
        else:
            force_use = False

        logger.info(">>>>>> RAW files download")

        self.set_tmp_dirs()
        self.clean_tmp_dirs()

        self.guess_local_raw()
        self.guess_remote_raw()
        self.check_local_files()
        self.filter_ok_out()
        self.invalidate_small_local_files()

        n_ok_inp = (self.table["ok_inp"]).sum()
        n_not_ok_inp = np.logical_not(self.table["ok_inp"]).sum()

        logger.info(
            "%6i files will be downloaded, %6i files are excluded",
            n_ok_inp,
            n_not_ok_inp,
        )

        if verbose:
            self.print_table()

        ping_out = self.ping_remote()
        if not ping_out:
            return None

        lock = self.create_lockfile()

        ###############################
        #### DOWNLOAD CORE a.k.a FETCH
        lock.acquire()
        try:
            self.fetch_remote_files(force_download=force_use)
        finally:
            lock.release()
            os.remove(lock.lock_file)
        ###############################

        if verbose:
            self.print_table()

        return None
