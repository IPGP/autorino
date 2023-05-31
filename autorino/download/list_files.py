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

# Create a logger object.
import logging
logger = logging.getLogger(__name__)



def list_remote_files_ftp(hostname, remote_dir, username, password):
    # connect to FTP server
    ftp = ftplib.FTP(hostname.replace('ftp://',""))
    ftp.login(username, password)
    
    # change to remote directory
    ftp.cwd(remote_dir)
    
    # retrieve list of files
    file_list = ftp.nlst()
    
    file_list = ["/".join((hostname, remote_dir, f)) for f in file_list]
        
    # close connection
    ftp.quit()
    
    return file_list

import requests
from bs4 import BeautifulSoup

def list_remote_files_http(host_name,remote_dir):

    url = os.path.join(host_name,remote_dir)
    
    logger.debug("HTTP file list:",url)
    
    # send HTTP request
    response = requests.get(url)
    
    # parse HTML response
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # extract list of files
    file_list = [link.get('href') for link in soup.find_all('a') if link.get('href') != '../']
    file_list = clean_remote_file_http(file_list)
    file_list = [host_name + f for f in file_list][1:] # remove the 1st element, which is the folder itself
        
    #fsize_list = [file_size_file_http(f) for f in file_list]
    
    return file_list#, fsize_list

def clean_remote_file_http(file_list_in):
    file_list = []
    for f in file_list_in:
        file_list.append(f.split('?')[0])
    file_list = list(sorted(set(file_list)))
    return file_list

def size_remote_file_http(url_list_in):
    size_url = []
    for url in url_list_in:
        req = urllib.request.Request(url, method='HEAD')
        f = urllib.request.urlopen(req)
        size_url.append(f.headers['Content-Length'])
    return size_url


import urllib.request

from tqdm import tqdm


class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download_url(url, output_path):
    with DownloadProgressBar(unit='B',
                             unit_scale=True,
                             miniters=1,
                             desc=url.split('/')[-1]) as t:
        urllib.request.urlretrieve(url,
                                   filename=output_path,
                                   reporthook=t.update_to)







def download(url: str, out_dir: str):
    resp = requests.get(url, stream=True)
    total = int(resp.headers.get('content-length', 0))
    fname = os.path.basename(url)
    fpath = os.path.join(out_dir,fname)
    
    # Can also replace 'file' with a io.BytesIO object
    with open(fpath, 'wb') as file, tqdm(
        desc=fpath,
        total=total,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in resp.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)
            
            
from tqdm import tqdm
from ftplib import FTP

def ftp_callback(data):
    ftp_callback.bytes_transferred += len(data)

def download_file_ftp(url, output_dir,username, password):
    # Check if URL is HTTP or FTP
    url = Path(url)
    print("BBBB",url.parents[-1])

    url_dir = url.relative_to(url.parents[-1]).parent
    
    print("BBBB",url_dir)
    
    ftp = ftplib.FTP(url_host)
    ftp.login(username, password)
    ftp.cwd(url_dir)
    filename = url.name
    
    file_size = ftp.size(filename)
    output_path = os.path.join(output_dir, filename)
    with open(output_path, 'wb') as f, tqdm(total=file_size,
                                            unit='B', 
                                            unit_scale=True,
                                            desc=filename) as pbar:
        ftp_callback.bytes_transferred = 0
        ftp.retrbinary('RETR ' + filename, lambda data: (f.write(data), pbar.update(len(data))), 1024)
    ftp.quit()
    
    
    
    
    # def download_url(url, output_path):
    # with DownloadProgressBar(unit='B',
                             # unit_scale=True,
                             # miniters=1,
                             # desc=url.split('/')[-1]) as t:
        # urllib.request.urlretrieve(url,
                                   # filename=output_path,
                                   # reporthook=t.update_to)


def download_file_http(url, output_dir):
    # Get file size
    response = requests.head(url)
    file_size = int(response.headers.get('content-length', 0))
    # Construct output path
    filename = url.split('/')[-1]
    output_path = os.path.join(output_dir, filename)
    # Download file with progress bar
    response = requests.get(url, stream=True)
    with open(output_path, 'wb') as f, tqdm(total=file_size,
                                            unit='B', 
                                            unit_scale=True,
                                            desc=filename) as pbar:
        for data in response.iter_content(chunk_size=1024):
            f.write(data)
            pbar.update(len(data))

############################################################
protocol = "http"
hostname="http://gps-abd.terrain.ovsg.univ-ag.fr/"
remote_dir="download/Internal/%Y%m/"
sta_user=""
sta_pass=""

protocol = "http"
remote_dir="download/Internal/%Y%m/"
hostname="http://gps-dsd.terrain.ovsg.univ-ag.fr"
sta_user=""
sta_pass=""

protocol = "http"
remote_dir="download/Internal/%Y%m/"
hostname="http://195.83.190.74"
sta_user=""
sta_pass=""

#AGAL
protocol = "http"
remote_dir="download/Internal/%Y%m/"
hostname="http://10.0.76.158"
sta_user=""
sta_pass=""



# PSA1
protocol = "http"
remote_dir="download/Internal/%Y%m/"
hostname="http://gps-psa.terrain.ovsg.univ-ag.fr"

# HOUE
protocol = "ftp"
remote_dir="/SD Card/Data/HOUE_30s_MDB/<SITE>/%Y/%m/%d"
hostname="gps-houe.terrain.ovsg.univ-ag.fr"
sta_user="root"
sta_pass="ovsg13;:"


now = dt.datetime.now() - dt.timedelta(days=30)

remote_dir_use = now.strftime(remote_dir)


transtab = dict()
transtab["<SITE>"] = "HOUE"

#remote_dir_use.translate(str.maketrans(transtab))

for k,v in transtab.items():
    remote_dir_use = remote_dir_use.replace(k,v)


output_path = "/home/gps/tests_pierres/dltest"
output_path = "/home/psakicki/aaa_FOURBI"
output_path = "/home/gps/tests_pierres/dltest"

if protocol == "http":
    list_ = list_remote_files_http(hostname,remote_dir_use)
    download_file_http(list_[0], output_path)
    download(list_[0], output_path)

elif protocol == "ftp":    
    list_ = list_remote_files_ftp(hostname,remote_dir_use,sta_user,sta_pass)
    download_file_ftp(list_[0], output_path, sta_user, sta_pass)
#print(list_)



#download_url(list_[1], output_path)
#download_url(list_[0], output_path + "/tototototo")



print("AAAAAAAAAAA",list_,sta_user,sta_pass)


