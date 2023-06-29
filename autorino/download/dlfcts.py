#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 27 09:16:34 2023

@author: psakicki
"""

import ftplib
import os
import datetime as dt 
import hashlib
import urllib
import pandas
from pathlib import Path
import urllib.request                 
from tqdm import tqdm
from ftplib import FTP
import requests
from bs4 import BeautifulSoup
from tqdm.contrib.logging import logging_redirect_tqdm
import io
# Create a logger object.
import logging
logger = logging.getLogger(__name__)





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
    buf = ''
    def __init__(self,logger,level=None):
        super(TqdmToLogger, self).__init__()
        self.logger = logger
        self.level = level or logging.INFO
    def write(self,buf):
        self.buf = buf.strip('\r\n\t ')
    def flush(self):
        self.logger.log(self.level, self.buf)

############# list remote files

def list_remote_files_ftp(host_name, remote_dir, username, password):
    # clean hostname & remote_dir
    remote_dir = remote_dir.replace(host_name,"")
    host_name = host_name.replace('ftp://',"")
    host_name = host_name.replace('/',"")
    remote_dir = remote_dir.replace(host_name,"")
    
    # connect to FTP server
    ftp = ftplib.FTP(host_name)
    ftp.login(username, password)
    
    # change to remote directory
    ftp.cwd(remote_dir)
    
    # retrieve list of files
    file_list = ftp.nlst()
    
    file_list = ["/".join((host_name, remote_dir, f)) for f in file_list]
        
    # close connection
    ftp.quit()
    
    return file_list

def list_remote_files_http(host_name,remote_dir):

    url = os.path.join(host_name,remote_dir)
    
    logger.debug("HTTP file list: %s",url)
        
    # send HTTP request
    response = requests.get(url)
    
    # parse HTML response
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # extract list of files
    def _parse_remote_file_http(file_list_in):
        """
        Internal function to parse the raw response of the remote file list
        """
        file_list = []
        for f in file_list_in:
            file_list.append(f.split('?')[0])
        file_list = list(sorted(set(file_list)))
        return file_list
    
    file_list = [link.get('href') for link in soup.find_all('a') if link.get('href') != '../']
    file_list = _parse_remote_file_http(file_list)
    file_list = [host_name + f for f in file_list][1:] # remove the 1st element, which is the folder itself
        
    #fsize_list = [file_size_file_http(f) for f in file_list]
    
    return file_list#, fsize_list


############# get size remote files

def size_remote_file_http(url):
    req = urllib.request.Request(url, method='HEAD')
    f = urllib.request.urlopen(req)
    size_url.append(f.headers['Content-Length'])
    return size_url

############# download remote file

def download_file_ftp(url, output_dir,username, password):
    ##### Check if URL is HTTP or FTP
    url = Path(url)
    url_host = str(url.parts[0])
    url_dir  = str(Path(*url.parts[1:-1]))
    
    ftp = ftplib.FTP(url_host)
    ftp.login(username, password)
    ftp.cwd(url_dir)
    filename = url.name
    
    def _ftp_callback(data):
        _ftp_callback.bytes_transferred += len(data)
    
    file_size = ftp.size(filename)

    output_path = os.path.join(output_dir, filename)
    f = open(output_path, 'wb')

    #tqdm_out = TqdmToLogger(logger,level=logging.INFO)
    with tqdm(total=file_size,
               unit='B', 
               unit_scale=True,
               desc=filename) as pbar:
                    
        _ftp_callback.bytes_transferred = 0
        ftp.retrbinary('RETR ' + filename, lambda data: (f.write(data), pbar.update(len(data))), 1024)
        ftp.quit()
        
    f.close()
    return output_path


def download_file_http(url, output_dir):
    # Get file size
    response = requests.head(url)
    file_size = int(response.headers.get('content-length', 0))
    # Construct output path
    filename = url.split('/')[-1]
    output_path = os.path.join(output_dir, filename)
    # Download file with progress bar
    response = requests.get(url, stream=True)
    
    f = open(output_path, 'wb')
    
    #tqdm_out = TqdmToLogger(logger,level=logging.INFO)
    with tqdm(total=file_size, unit='B',
              unit_scale=True, desc=filename) as pbar:
        for data in response.iter_content(chunk_size=1024):
            f.write(data)
            pbar.update(len(data))
                
    f.close()
    return output_path
