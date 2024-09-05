#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 27 09:16:34 2023

@author: psakic
"""

import ftplib
import io

import os
import socket
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

logger = logging.getLogger(__name__)
logger.setLevel(aroenv.aro_env_dict["general"]["log_level"])


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

    ### add the protocol if missing
    if not (hostname_inp.startswith("http") or hostname_inp.startswith("ftp")):
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
    url_host_inp, username=None, password=None, timeout=15, max_try=3, sleep_time=5
):
    """
    create an FTP object, and retry in case of a timeout
    """

    try_count = 0
    while True:
        try:
            ftp = ftplib.FTP(url_host_inp, timeout=timeout)
            if username and password:
                ftp.login(username, password)
            return ftp
        except TimeoutError as e:
            try_count += 1
            if try_count > max_try:
                raise e
            else:
                print(e)
                time.sleep(sleep_time)
        #
        except OSError as e:
            logger.error("Unable to create FTP object: %s", str(e))
            return None


def list_remote_ftp(
    host_name, remote_dir, username, password, timeout=15, max_try=3, ftp_obj_inp=None
):
    # clean hostname & inp_dir_parent
    # MUST BE IMPROVED !!!
    remote_dir = remote_dir.replace(host_name, "")
    host_name = host_name.replace("ftp://", "")
    host_name = host_name.replace("/", "")
    remote_dir = remote_dir.replace(host_name, "")

    # connect to FTP server
    if ftp_obj_inp:
        ftp_obj = ftp_obj_inp
    else:
        ftp_obj = ftp_create_obj(
            host_name, username, password, timeout=timeout, max_try=max_try
        )

    if not ftp_obj:
        logger.error("FTP connection failed for %s", host_name)
        return []

    # change to remote directory
    ftp_obj.cwd(remote_dir)

    # retrieve list of files
    file_list = ftp_obj.nlst()

    file_list = ["/".join((host_name, remote_dir, f)) for f in file_list]

    # close connection
    ftp_obj.quit()

    return file_list

def download_ftp(
    url,
    output_dir,
    username,
    password,
    timeout=15,
    max_try=3,
    sleep_time=5,
    ftp_obj_inp=None,
):
    urlp = urlparse(url)
    url_host = urlp.netloc
    url_dir = os.path.dirname(urlp.path)[1:]
    url_fname = os.path.basename(urlp.path)

    if ftp_obj_inp:
        ftp_obj = ftp_obj_inp
    else:
        ftp_obj = ftp_create_obj(
            url_host,
            username=username,
            password=password,
            timeout=timeout,
            max_try=max_try,
            sleep_time=sleep_time,
        )

    if not ftp_obj:
        logger.error("FTP connection failed for %s", url)
        return ""

    ftp_obj.cwd(url_dir)
    filename = url_fname

    def _ftp_callback(data):
        _ftp_callback.bytes_transferred += len(data)

    file_size = ftp_obj.size(filename)

    output_path = os.path.join(output_dir, filename)
    # f = open(output_path, 'wb')
    # tqdm_out = TqdmToLogger(logger,level=logging.INFO)
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
        except (
            ftplib.error_temp,
            ftplib.error_reply,
            BrokenPipeError,
            socket.timeout,
        ) as e:
            try_count += 1
            if try_count > max_try:
                raise AutorinoDownloadError
            else:
                logger.warning(
                    "download failed (%s), try %i/%i", str(e), try_count, max_try
                )
                time.sleep(sleep_time)

    ftp_obj.quit()
    f.close()
    return output_path


 #  _    _ _______ _______ _____
 # | |  | |__   __|__   __|  __ \
 # | |__| |  | |     | |  | |__) |
 # |  __  |  | |     | |  |  ___/
 # | |  | |  | |     | |  | |
 # |_|  |_|  |_|     |_|  |_|
 #



def list_remote_http(host_name, remote_dir):

    url = os.path.join(host_name, remote_dir)
    url = "http://" + host_name + "/" + remote_dir

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
    file_list = [host_name + f for f in file_list][
        1:
    ]  # remove the 1st element, which is the folder itself

    # fsize_list = [file_size_file_http(f) for f in file_list]

    return file_list  # , fsize_list


def size_remote_file_http(url):
    req = urllib.request.Request(url, method="HEAD")
    f = urllib.request.urlopen(req)
    return f.headers["Content-Length"]


def download_http(url, output_dir, timeout=15, max_try=3, sleep_time=5):
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

def ping(host, timeout=20):
    """
    Executes the ping command and captures the output.

    This function sends a single ICMP echo request to the specified host and captures the round-trip time (RTT) from the output.

    Parameters
    ----------
    host : str
        The hostname or IP address to ping.
    timeout : int, optional
        The timeout for the ping command in seconds. Default is 10 seconds.

    Returns
    -------
    float or None
        The round-trip time (RTT) in seconds if the ping is successful, otherwise None.
    """

    result = subprocess.run(
        ["ping", "-c", "1", "-W", str(timeout), host],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    match = re.search(r"time=(\d+\.?\d*)\s*ms", result.stdout)

    if match:
        return float(match.group(1)) * 10**-3
    else:
        return None
