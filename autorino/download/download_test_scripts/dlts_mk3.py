#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime as dt
import pandas as pd
import numpy as np
import os
from autorino import download as ardl

# Create a logger object.
import logging
logger = logging.getLogger(__name__)


def _dir_translator_date(dir_input,date):
    dir_translated = str(dir_input)
    dir_translated = date.strftime(dir_translated)
    return dir_translated

def _dir_translator_keywords(dir_input,translator_dict):
    dir_translated = str(dir_input)
    for k,v in translator_dict.items():
        dir_translated = dir_translated.replace("<"+k+">",v)
    return dir_translated
    
class DateRange:
    def __init__(self,date1,date2,period="01D",round_method="ceil"):
        self.period = period
        self.round_method = round_method
        self.date_start = np.min((date1,date2))
        self.date_end = np.max((date1,date2))
        #test sur session period !!!!!!    
    
    
    ############ getters and setters 
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
        
    ########### methods
    def date_range_list(self):
        daterange=pd.date_range(self.date_start,
                                self.date_end,
                                freq=self.period)
        return list(daterange)
    

class StationTest:
    def __init__(self,protocol,hostname,remote_dir,remote_fname,
                 sta_user,sta_pass,site4,session_period):

        self.protocol = protocol
        self.hostname = hostname
        self.remote_dir = remote_dir
        self.remote_fname = remote_fname
        self.sta_user = sta_user
        self.sta_pass = sta_pass  
        self.site4 = site4           
        self.session_period = session_period
        self.translate_dict = None
        
    #test sur session period !!!!!! sur protocol !!!

    ############ getters and setters 
    @property
    def translate_dict(self):
        return self._translate_dict
        
    @translate_dict.setter
    def translate_dict(self,value):
        self._translate_dict = dict()
        self._translate_dict["SITE4"] = self.site4.upper()

    ########### methods        
    def guess_remote_files(self,daterange_in,set_as_req_list=):

        rmot_paths_list = []
        for date in daterange_in.date_range_list():
            
            ### guess the potential directories
            rmot_dir_use = str(self.remote_dir)
            rmot_dir_use = _dir_translator_date(rmot_dir_use,date)
            rmot_dir_use = _dir_translator_keywords(rmot_dir_use,
                                                      self.translate_dict)
            ### guess the potential filenames
            rmot_fname_use = str(self.remote_fname)
            rmot_fname_use = _dir_translator_date(rmot_fname_use,
                                                  date)
            rmot_fname_use = _dir_translator_keywords(rmot_fname_use,
                                                      self.translate_dict)
                                                                                                            
            rmot_path_use = os.path.join(rmot_dir_use,rmot_fname_use)
                                                      
            rmot_paths_list.append(rmot_path_use)
            
        rmot_paths_list = sorted(list(set(rmot_paths_list)))
            
        return rmot_paths_list
        
    def list_remote_directories(self,daterange_in):
        rmot_dir_list = []
        for date in daterange_in.date_range_list():
            rmot_dir_use = str(self.remote_dirg)
            rmot_dir_use = _dir_translator_date(rmot_dir_use,date)
            rmot_dir_use = _dir_translator_keywords(rmot_dir_use,
                                                      self.translate_dict)
            rmot_dir_list.append(rmot_dir_use)
        rmot_dir_list = sorted(list(set(rmot_dir_list)))
            
        return rmot_dir_list

    def list_remote_files(self,daterange_in):
        rmot_dir_list = self.list_rmot_directories(daterange_in)

        rmot_files_list = []
        for rmot_dir_use in rmot_dir_list:
            print(rmot_dir_use)
            if self.protocol == "http":
                list_ = ardl.list_rmot_files_http(self.hostname,
                                                    rmot_dir_use)
                rmot_files_list = rmot_files_list + list_
            elif self.protocol == "ftp":
                list_ = ardl.list_rmot_files_ftp(self.hostname,
                                                   rmot_dir_use,
                                                   self.sta_user,
                                                   self.sta_pass)
                rmot_files_list = rmot_files_list + list_

            else:
                logger.error("wrong protocol")
        return rmot_files_list

    def download_remote_files(self,daterange_in,out_dir,
                              filter_files=True):
        
        download_files_list = []
        rmot_files_list = self.list_rmot_files(daterange_in)
                
        for  rmot_file  in rmot_files_list:
            if self.protocol == "http":
                file_dl = ardl.download_file_http(rmot_file,
                                                  out_dir)
                download_files_list.append(file_dl)
            elif self.protocol == "ftp":
                file_dl = ardl.download_file_ftp(rmot_file,
                                               out_dir,
                                               self.sta_user,
                                               self.sta_pass)
                download_files_list.append(file_dl)

            else:
                logger.error("wrong protocol")
        return download_files_list
        
############################################################
# protocol = "http"
# hostname="http://gps-abd.terrain.ovsg.univ-ag.fr/"
# remote_dir="download/Internal/%Y%m/"
# sta_user=""
# sta_pass=""

# protocol = "http"
# remote_dir="download/Internal/%Y%m/"
# hostname="http://gps-dsd.terrain.ovsg.univ-ag.fr"
# sta_user=""
# sta_pass=""

# protocol = "http"
# remote_dir="download/Internal/%Y%m/"
# hostname="http://195.83.190.74"
# sta_user=""
# sta_pass=""

# # HOUE
# protocol = "ftp"
# remote_dir="/SD Card/Data/HOUE_30s_MDB/<SITE4>/%Y/%m/%d"
# hostname="gps-houe.terrain.ovsg.univ-ag.fr"
# sta_user="root"
# sta_pass="ovsg13;:"


#AGAL
protocol = "http"
remote_dir="download/Internal/%Y%m/"
hostname="http://10.0.76.158"
sta_user=""
sta_pass=""
site4="AGAL"
session_period="1D"


#######' HOUE
protocol = "ftp"
hostname="gps-houe.terrain.ovsg.univ-ag.fr"
remote_dir="/SD Card/Data/HOUE_30s_MDB/<SITE4>/%Y/%m/%d"
sta_user="root"
sta_pass="ovsg13;:"
site4="HOUE"
session_period="1D"

# PSA1
protocol = "http"
hostname="http://gps-psa.terrain.ovsg.univ-ag.fr"
remote_dir="download/Internal/%Y%m/"
remote_fname="<SITE4>______%Y%m%d%H%M%SA.T02"
sta_user=""
sta_pass=""
site4="PSA1"
session_period="1D"



########################################################################

STAT = StationTest(protocol = protocol,
remote_dir=remote_dir,
hostname=hostname,
sta_user=sta_user,
sta_pass=sta_pass,
site4=site4,
session_period=session_period,
remote_fname=remote_fname)

output_path = "/home/gps/tests_pierres/dltest"

now = dt.datetime.now() - dt.timedelta(days=10)
date_interest = now - dt.timedelta(days=2)
DR = DateRange(date_interest,now)

#L = STAT.list_remote_files(DR)
Lguess = STAT.guess_remote_files(DR)
print(Lguess)
#STAT.download_remote_files(DR,output_path)

