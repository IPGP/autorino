#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime as dt

import numpy as np
import pandas as pd

from autorino import download as ardl


def _dir_translator_date(dir_input,date):
    dir_translated = str(dir_input)
    dir_translated = date.strftime(dir_translated)
    return dir_translated

def _dir_translator_keywords(dir_input,translator_dict):
    dir_translated = str(dir_input)
    for k,v in transtab.items():
        dir_translated = dir_translated.replace(k,v)
    return dir_translated
    
    
class DateRange:
    
    def __init__(self,date1,date2,period="01D",round_method="ceil"):
        self.period = period
        self.date_start = np.min((date1,date2))
        self.date_end = np.max((date1,date2))
        #test sur session period !!!!!!    
    
    @property
    def date_start(self):
        return self._date_start.ceil(self.period)
        
    @date_start.setter
    def date_start(self,value):
        self._date_start = pd.Timestamp(value)
    
    @property
    def date_end(self):
        return self._date_end.ceil(self.period)
        
    @date_end.setter
    def date_end(self,value):
        self._date_end = pd.Timestamp(value)
        
        
    def date_range_list(self):
        daterange=pd.date_range(self.date_start,
                                self.date_end,
                                freq=self.period)
        return list(daterange)
    

class StationTest:
    def __init__(self,protocol,hostname,remote_dir,
                 sta_user,sta_pass,site4,session_period):
        # self.protocol = self.set_protocol(protocol)
        # self.set_hostname(hostname)
        # self.set_remote_dir(inp_dir_parent)
        # self.set_sta_user(sta_user)
        # self.set_sta_pass(sta_pass)
        
        self.protocol = protocol
        self.hostname = hostname
        self.remote_dir_generic = remote_dir
        self.sta_user = sta_user
        self.sta_pass = sta_pass  
        self.site4 = site4           
        self.session_period = session_period
        
    #test sur session period !!!!!!
    


    def list_remote_files(self,daterange_in):
        
        remote_dir_list = []
        for date in daterange_in.date_range_list():
            remote_dir_use = str(self.remote_dir_generic)
            transtab = dict()
            transtab["<SITE4>"] = self.site4
            remote_dir_use = _dir_translator_date(remote_dir_use,date)
            remote_dir_use = _dir_translator_keywords(remote_dir_use,transtab)
            remote_dir_list.append(remote_dir_use)
         
        remote_files_list = []
        for remote_dir_use in remote_dir_list:
            print(remote_dir_use)
            if self.protocol == "http":
                list_ = ardl.list_remote_http(self.hostname,
                                              remote_dir_use)
                remote_files_list = remote_files_list + list_
            elif self.protocol == "ftp":
                list_ = ardl.list_remote_ftp(self.hostname,
                                             remote_dir_use,
                                             self.sta_user,
                                             self.sta_pass)
                remote_files_list = remote_files_list + list_

            else:
                print("XXXXXXXXXXXXXXXXXXXX wrong protocol")
                
        return remote_files_list


            
        
        
    # ### setters
    # def set_protocol(self,protocol):
        # self.protocol = protocol

    # def set_hostname(self,hostname):
        # self.hostname = hostname   
             
    # def set_remote_dir(self,inp_dir_parent):
        # self.inp_dir_parent = inp_dir_parent
    
    # def set_sta_user(self,sta_user):
        # self.set_sta_user = sta_user

    # def set_sta_pass(self,sta_pass):
        # self.set_sta_pass = sta_pass
        
        
       

############################################################
# protocol = "http"
# hostname="http://gps-abd.terrain.ovsg.univ-ag.fr/"
# inp_dir_parent="download/Internal/%Y%m/"
# sta_user=""
# sta_pass=""

# protocol = "http"
# inp_dir_parent="download/Internal/%Y%m/"
# hostname="http://gps-dsd.terrain.ovsg.univ-ag.fr"
# sta_user=""
# sta_pass=""

# protocol = "http"
# inp_dir_parent="download/Internal/%Y%m/"
# hostname="http://195.83.190.74"
# sta_user=""
# sta_pass=""

# #AGAL
# protocol = "http"
# inp_dir_parent="download/Internal/%Y%m/"
# hostname="http://10.0.76.158"
# sta_user=""
# sta_pass=""

# # PSA1
# protocol = "http"
# inp_dir_parent="download/Internal/%Y%m/"
# hostname="http://gps-psa.terrain.ovsg.univ-ag.fr"

# # HOUE
# protocol = "ftp"
# inp_dir_parent="/SD Card/Data/HOUE_30s_MDB/<SITE4>/%Y/%m/%d"
# hostname="gps-houe.terrain.ovsg.univ-ag.fr"
# sta_user="root"
# sta_pass="ovsg13;:"



STAT = StationTest(protocol = "ftp",
remote_dir="/SD Card/Data/HOUE_30s_MDB/<SITE4>/%Y/%m/%d",
hostname="gps-houe.terrain.ovsg.univ-ag.fr",
sta_user="root",
sta_pass="ovsg13;:",
site4="HOUE",
session_period="1D")



now = dt.datetime.now() - dt.timedelta(days=10)
date_interest = now - dt.timedelta(days=30)
# remote_dir_use = now.strftime(inp_dir_parent)

DR = DateRange(date_interest,now)

print(DR.date_range_list())

transtab = dict()
transtab["<SITE4>"] = "HOUE"

L = STAT.list_remote_files(DR)
print(L)


output_path = "/home/gps/tests_pierres/dltest"

# if protocol == "http":
    # list_ = ardl.list_remote_http(hostname,remote_dir_use)
    # print(list_)
    # print(size_remote_file_http([list_[0]]))
    # ardl.download_http(list_[0], output_path)
    # #download(list_[0], output_path)

# elif protocol == "ftp":    
    # list_ = ardl.list_remote_ftp(hostname,remote_dir_use,sta_user,sta_pass)
    # print(list_)
    # ardl.download_ftp(list_[0], output_path, sta_user, sta_pass)
    
    
#print("downloaded list",list_,sta_user,sta_pass)
