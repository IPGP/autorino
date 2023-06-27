#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime as dt
from autorino import download as ardl


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

if protocol == "http":
    list_ = ardl.list_remote_files_http(hostname,remote_dir_use)
    print(list_)
    print(size_remote_file_http([list_[0]]))
    ardl.download_file_http(list_[0], output_path)
    #download(list_[0], output_path)

elif protocol == "ftp":    
    list_ = ardl.list_remote_files_ftp(hostname,remote_dir_use,sta_user,sta_pass)
    print(list_)
    ardl.download_file_ftp(list_[0], output_path, sta_user, sta_pass)
    
    
#print("downloaded list",list_,sta_user,sta_pass)
