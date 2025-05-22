#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 27 09:16:34 2023

@author: psakic
"""

import ftplib
import io

import os

# import socket
import urllib
import urllib.request
import time
from urllib.parse import urlparse
import subprocess
import re

import requests
from bs4 import BeautifulSoup
import tqdm

#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger("autorino")
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])


# *****************************************************************************
# define Python user-defined exceptions
class AutorinoError(Exception):
    pass


class AutorinoDownloadError(AutorinoError):
    pass


class TqdmToLogger(io.StringIO):
    """
    Output stream for TQDM which will output to logger module instead of
    the StdOut.
    """

    logger = None
    level = None
    buf = ""

    def __init__(self, logger_inp, level=None):
        super(TqdmToLogger, self).__init__()
        self.logger = logger_inp
        self.level = level or logging.INFO

    def write(self, buf):
        self.buf = buf.strip("\r\n\t ")

    def flush(self):
        self.logger.log(self.level, self.buf)


def join_url(protocol_inp, hostname_inp, dir_inp, fname_inp):
    """
    a wrapper to classical join to format correctly the URL
    """
    # urltambouille
    ### add the protocol if missing
    if protocol_inp and not (
        hostname_inp.startswith("http") or hostname_inp.startswith("ftp")
    ):
        prot_n_host = protocol_inp + "://" + hostname_inp
    else:
        prot_n_host = hostname_inp

    ### remove (strip) slashs in the dir path
    dirr = dir_inp.strip("/")

    ### safty warning to check a stupid copy/paste
    if fname_inp in dirr:
        logger.warning("%s 's filename also appears in dirname", fname_inp)

    url_out = os.path.join(prot_n_host, dirr, fname_inp)

    return url_out


#  ______ _______ _____
# |  ____|__   __|  __ \
# | |__     | |  | |__) |
# |  __|    | |  |  ___/
# | |       | |  | |
# |_|       |_|  |_|


def ftp_create_obj(
    hostname_inp, username=None, password=None, timeout=15, max_try=3, sleep_time=5
):
    """
    Create an FTP object, and retry in case of a timeout.

    Parameters
    ----------
    hostname_inp : str
        The hostname of the FTP server.
    username : str, optional
        The username for FTP login. Default is None.
    password : str, optional
        The password for FTP login. Default is None.
    timeout : int, optional
        The timeout for FTP connection in seconds. Default is 15 seconds.
    max_try : int, optional
        The maximum number of retry attempts in case of failure. Default is 3.
    sleep_time : int, optional
        The sleep time between retry attempts in seconds. Default is 5 seconds.

    Returns
    -------
    ftplib.FTP or None
        The FTP object if the connection is successful, otherwise None.

    Raises
    ------
    TimeoutError
        If the connection fails after the maximum number of retry attempts.
    """
    try_count = 0
    while True:
        try:
            ftp = ftplib.FTP(hostname_inp, timeout=timeout)
            if (username is not None) and (password is not None):
                ftp.login(username, password)
            return ftp
        except TimeoutError as e:
            try_count += 1
            if try_count > max_try:
                raise e
            else:
                print(e)
                time.sleep(sleep_time)
        except (OSError, ftplib.error_perm, Exception) as e:
            logger.error("Unable to create FTP object: %s", str(e))
            return None

def list_remote_ftp(
    hostname,
    remote_dir,
    username=None,
    password=None,
    timeout=15,
    max_try=3,
    ftp_obj_inp=None,
):
    """
    List files in a remote FTP directory.

    Parameters
    ----------
    hostname : str
        The hostname of the FTP server.
    remote_dir : str
        The remote directory to list files from.
    username : str, optional
        The username for FTP login. Default is None.
    password : str, optional
        The password for FTP login. Default is None.
    timeout : int, optional
        The timeout for FTP connection in seconds. Default is 15 seconds.
    max_try : int, optional
        The maximum number of retry attempts in case of failure. Default is 3.
    ftp_obj_inp : ftplib.FTP, optional
        An existing FTP object to use for the connection. Default is None.

    Returns
    -------
    list
        A list of file paths in the remote directory.

    Raises
    ------
    AutorinoDownloadError
        If the FTP connection fails or if username/password are missing.
    """

    # Clean hostname and remote directory
    # legacy hostname_use defintion (urltambouille)
    # hostname_use = hostname.replace("ftp://", "")
    # hostname_use = hostname_use.replace("/", "")

    url_parsed = urlparse(hostname)
    if url_parsed.scheme:
        hostname_use = url_parsed.netloc
    else:
        hostname_use = url_parsed.path

    # be sure there is no hostname in the remote_dir
    remote_dir_use = remote_dir.replace(hostname, "")
    remote_dir_use = remote_dir_use.replace(hostname_use, "")

    # Connect to FTP server
    if ftp_obj_inp:
        disposable_ftp_obj = False
        ftp_obj = ftp_obj_inp
    elif username is not None and password is not None:
        disposable_ftp_obj = True
        ftp_obj = ftp_create_obj(
            hostname_inp=hostname_use,
            username=username,
            password=password,
            timeout=timeout,
            max_try=max_try,
        )
    else:
        logger.error(
            "unable to create FTP object, missing username/password or input object"
        )
        raise AutorinoDownloadError

    if not ftp_obj:
        logger.error("FTP connection failed for %s", hostname_use)
        return []

    # Change to remote directory
    try:
        ftp_obj.cwd(remote_dir_use)
    except ftplib.error_perm as e:
        logger.error("FTP directory change failed: %s", str(e))
        logger.error("Wished destination: %s", remote_dir_use)
        return []
    except EOFError as e:
        logger.error("FTP cwd failed: %s %s", remote_dir_use, str(e))
        return []



    # Retrieve list of files
    try:
        file_list_bulk = ftp_obj.nlst()
    except Exception as e:
        logger.error("FTP file list failed: %s", str(e))
        file_list_bulk = []

    # current directory (.) and parent directory (..) are removed anyway
    file_list_bulk = [f for f in file_list_bulk if f not in (".", "..")]
    file_list_join = [
        join_url("", hostname_use, remote_dir_use, f.split()[-1])
        for f in file_list_bulk
    ]
    # split()[-1] is necessary for Trimble files, to have just the filename and not the size, owner, etc.

    file_list = file_list_join

    # Close connection
    if disposable_ftp_obj:
        ftp_obj.quit()

    return list(file_list)


def download_ftp(
    url,
    output_dir,
    username=None,
    password=None,
    timeout=30,
    max_try=4,
    sleep_time=5,
    ftp_obj_inp=None,
):
    """
    Download a file from an FTP server with retry logic and progress bar.

    Parameters
    ----------
    url : str
        The URL of the file to download.
    output_dir : str
        The directory where the downloaded file will be saved.
    username : str
        The username for FTP login.
        Overrided by the ftp_obj_inp parameter.
    password : str
        The password for FTP login.
        Overrided by the ftp_obj_inp parameter.
    timeout : int, optional
        The timeout for FTP connection in seconds. Default is 15 seconds.
    max_try : int, optional
        The maximum number of retry attempts in case of failure. Default is 3.
    sleep_time : int, optional
        The sleep time between retry attempts in seconds. Default is 5 seconds.
    ftp_obj_inp : ftplib.FTP, optional
        An existing FTP object to use for the connection.
        Overrides the username and password parameters.
        Default is None.

    Returns
    -------
    str
        The path to the downloaded file, or an empty string if the download failed.
        If something goes wrong, the function will raise an AutorinoDownloadError
        (no empty string or None).

    Raises
    ------
    AutorinoDownloadError
        If the download fails after the maximum number of retry attempts.
    """

    def _ftp_callback(data):
        _ftp_callback.bytes_transferred += len(data)

    urlp = urlparse(url)
    url_host = urlp.netloc
    url_dir = os.path.dirname(urlp.path)  # [1:]
    url_fname = os.path.basename(urlp.path)

    # create the FTP object
    if ftp_obj_inp:
        disposable_ftp_obj = False
        ftp_obj = ftp_obj_inp
    elif username is not None and password is not None:
        disposable_ftp_obj = True
        ftp_obj = ftp_create_obj(
            url_host,
            username=username,
            password=password,
            timeout=timeout,
            max_try=max_try,
            sleep_time=sleep_time,
        )
    else:
        logger.error(
            "unable to create FTP object, missing username/password or input object"
        )
        raise AutorinoDownloadError

    # connect to the FTP server
    if not ftp_obj:
        logger.error("FTP connection failed for %s", url)
        raise AutorinoDownloadError

    # change to the remote directory
    try:
        ftp_obj.cwd(url_dir)
    except ftplib.error_perm as e:
        logger.error("FTP directory change failed: %s", str(e))
        logger.error("Wished destination: %s", url_dir)
        raise AutorinoDownloadError

    filename = url_fname
    ftp_obj.sendcmd("TYPE I")
    file_size = ftp_obj.size(filename)
    output_path = os.path.join(output_dir, filename)
    try_count = 0

    while True:
        try:
            with tqdm.tqdm(
                total=file_size, unit="B", unit_scale=True, desc=filename
            ) as pbar, open(output_path, "wb") as f:

                _ftp_callback.bytes_transferred = 0
                ftp_obj.retrbinary(
                    "RETR " + filename,
                    lambda data: (f.write(data), pbar.update(len(data))),
                    1024,
                )
                break
        # here are all the possible exceptions that can be raised
        except Exception as e:
            try_count += 1
            if try_count > max_try:
                logger.error("download failed, max try exceeded: %s", str(e))
                raise AutorinoDownloadError
                # this error will be handled by the upper function mono_fetch
            else:
                logger.warning(
                    "download failed (%s), try %i/%i", str(e), try_count, max_try
                )
                time.sleep(sleep_time)

    f.close()

    if disposable_ftp_obj:
        ftp_obj.quit()

    return output_path


#  _    _ _______ _______ _____
# | |  | |__   __|__   __|  __ \
# | |__| |  | |     | |  | |__) |
# |  __  |  | |     | |  |  ___/
# | |  | |  | |     | |  | |
# |_|  |_|  |_|     |_|  |_|
#


def list_remote_http(hostname, remote_dir):

    url = join_url("http", hostname, remote_dir, "")

    # legacy manual join (urltambouille
    # url = os.path.join(hostname, remote_dir)
    # url = "http://" + hostname + "/" + remote_dir

    logger.debug("HTTP file list: %s", url)

    # send HTTP request
    response = requests.get(url)

    # parse HTML response
    soup = BeautifulSoup(response.content, "html.parser")

    # extract list of files
    def _parse_remote_file_http(file_list_in):
        """
        Internal function to parse the raw response of the remote file list
        """
        fillis = []
        for f in file_list_in:
            fillis.append(f.split("?")[0])
        fillis = list(sorted(set(fillis)))
        return fillis

    file_list = [
        link.get("href") for link in soup.find_all("a") if link.get("href") != "../"
    ]
    file_list = _parse_remote_file_http(file_list)
    file_list = [hostname + f for f in file_list][
        1:
    ]  # remove the 1st element, which is the folder itself

    # fsize_list = [file_size_file_http(f) for f in file_list]

    return file_list  # , fsize_list


def size_remote_file_http(url):
    req = urllib.request.Request(url, method="HEAD")
    f = urllib.request.urlopen(req)
    return f.headers["Content-Length"]


def download_http(url, output_dir, timeout=120, max_try=4, sleep_time=5):
    """
    Download a file from an HTTP server with retry logic and progress bar.

    Parameters
    ----------
    url : str
        The URL of the file to download.
    output_dir : str
        The directory where the downloaded file will be saved.
    timeout : int, optional
        The timeout for the HTTP connection in seconds. Default is 120 seconds.
    max_try : int, optional
        The maximum number of retry attempts in case of failure. Default is 4.
    sleep_time : int, optional
        The sleep time between retry attempts in seconds. Default is 5 seconds.

    Returns
    -------
    str
        The path to the downloaded file, or an empty string if the download failed.

    Raises
    ------
    AutorinoDownloadError
        If the download fails after the maximum number of retry attempts.
    """
    # Get file size
    response = requests.head(url, timeout=timeout)
    file_size = int(response.headers.get("content-length", 0))

    # Construct output path
    filename = url.split("/")[-1]
    output_path = os.path.join(output_dir, filename)

    # Download file with progress bar
    try_count = 0
    while True:
        try:
            response = requests.get(url, stream=True, timeout=timeout)
            with open(output_path, "wb") as f:
                with tqdm.tqdm(
                    total=file_size, unit="B", unit_scale=True, desc=filename
                ) as pbar:
                    for data in response.iter_content(chunk_size=1024):
                        f.write(data)
                        pbar.update(len(data))
            break
        except requests.exceptions.RequestException as e:
            try_count += 1
            if try_count > max_try:
                raise AutorinoDownloadError

            logger.warning(
                "download failed (%s), try %i/%i", str(e), try_count, max_try
            )
            time.sleep(sleep_time)

    return output_path


#  _____ _
# |  __ (_)
# | |__) | _ __   __ _
# |  ___/ | '_ \ / _` |
# | |   | | | | | (_| |
# |_|   |_|_| |_|\__, |
#                 __/ |
#                |___/


def ping(host, ping_timeout=20):
    """
    Executes the ping command and captures the output.

    This function sends a single ICMP echo request to the specified
    host and captures the round-trip time (RTT) from the output.

    Parameters
    ----------
    host : str
        The hostname or IP address to ping.
    ping_timeout : int, optional
        The timeout for the ping command in seconds. Default is 10 seconds.

    Returns
    -------
    float or None
        The round-trip time (RTT) in seconds if the ping is successful,
        otherwise None.
    """

    result = subprocess.run(
        ["ping", "-c", "1", "-W", str(ping_timeout), host],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    match = re.search(r"time=(\d+\.?\d*)\s*ms", result.stdout)

    if match:
        return float(match.group(1)) * 10**-3
    else:
        return None


def check_file_size(file_path, min_size=1000):
    """
    Check the size of a file and log a warning if it is too
    small to be useful.

    Parameters
    ----------
    file_path : str
        The path to the file to check.
    min_size : int, optional
        The minimum file size in bytes. Default is 1000 bytes.

    Returns
    -------
    ok_size : bool
        True if the file size is acceptable, otherwise False.
    file_size : int
        The size of the file in bytes

    """
    file_size = os.path.getsize(file_path)
    if file_size < min_size:
        logger.error(
            "Excluded small file (%iB < %iB): %s", file_size, min_size, file_path
        )
        ok_size = False
    else:
        ok_size = True

    return ok_size, file_size
