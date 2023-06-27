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
        
    def __repr__(self):
        return "date range from {} to {}, period {}".format(self.date_start,self.date_end,self.period)
    
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
    
class RequestGnss():
    def __init__(self,session,date_range,out_dir):
        self.date_range = date_range
        self.session = session
        self.out_dir = out_dir
        self.req_remote_files = []
        self.req_local_files = []
    
    ########### methods        
    def guess_remote_files(self,set_req_remote_files=True):
        
        if not self.session.remote_fname:
            logger.warning("generic filename empty for %s, the guessed remote filepaths will be wrong",self.session)
        
        rmot_paths_list = []
        for date in self.date_range.date_range_list():
            ### guess the potential directories
            rmot_dir_use = str(self.session.remote_dir)
            rmot_dir_use = _dir_translator_date(rmot_dir_use,date)
            rmot_dir_use = _dir_translator_keywords(rmot_dir_use,
                                                    self.session.translate_dict)
            ### guess the potential filenames
            rmot_fname_use = str(self.session.remote_fname)
            rmot_fname_use = _dir_translator_date(rmot_fname_use,
                                                  date)
            rmot_fname_use = _dir_translator_keywords(rmot_fname_use,
                                                      self.session.translate_dict)
                                                                                                            
            rmot_path_use = os.path.join(self.session.hostname,
                                         rmot_dir_use,
                                         rmot_fname_use)
                                                      
            rmot_paths_list.append(rmot_path_use)
            
            logger.debug("remote file/dir guessed: %s",rmot_path_use)
            
        rmot_paths_list = sorted(list(set(rmot_paths_list)))
        
        if set_req_remote_files:
            self.req_remote_files = rmot_paths_list
            
        logger.info("remote files/dirs guessed: %s",len(rmot_paths_list))
        return rmot_paths_list
        
    def guess_remote_directories(self,set_req_remote_files=True):
        
        ### must be merged with fct above
        
        rmot_dir_list = []
        for date in self.date_range.date_range_list():
            rmot_dir_use = str(self.session.remote_dir)
            rmot_dir_use = _dir_translator_date(rmot_dir_use,date)
            rmot_dir_use = _dir_translator_keywords(rmot_dir_use,
                                                    self.session.translate_dict)
            rmot_dir_list.append(rmot_dir_use)
        rmot_dir_list = sorted(list(set(rmot_dir_list)))
                    
        return rmot_dir_list

    def ask_remote_files(self,set_req_remote_files=True):
        rmot_dir_list = self.guess_remote_directories()
        rmot_files_list = []
        for rmot_dir_use in rmot_dir_list:
            if self.session.protocol == "http":
                list_ = ardl.list_remote_files_http(self.session.hostname,
                                                  rmot_dir_use)
                rmot_files_list = rmot_files_list + list_
            elif self.session.protocol == "ftp":
                list_ = ardl.list_remote_files_ftp(self.session.hostname,
                                                 rmot_dir_use,
                                                 self.session.sta_user,
                                                 self.session.sta_pass)
                rmot_files_list = rmot_files_list + list_

            else:
                logger.error("wrong protocol")
            logger.debug("remote files found on rec: %s",list_)
        
        if set_req_remote_files:
            self.req_remote_files = rmot_files_list
        
        logger.info("remote files found on rec: %s",len(rmot_files_list))
        return rmot_files_list

    def download_remote_files(self):
        download_files_list = []
        rmot_files_list = self.req_remote_files
                
        for rmot_file in rmot_files_list:
            if self.session.protocol == "http":
                file_dl = ardl.download_file_http(rmot_file,
                                                  self.out_dir)
                download_files_list.append(file_dl)
            elif self.session.protocol == "ftp":
                file_dl = ardl.download_file_ftp(rmot_file,
                                               self.out_dir,
                                               self.session.sta_user,
                                               self.session.sta_pass)
                download_files_list.append(file_dl)

            else:
                logger.error("wrong protocol")
                
        self.req_local_files = download_files_list
        
        return download_files_list

class SessionGnss:
    def __init__(self,protocol,hostname,remote_dir,remote_fname,
                 sta_user,sta_pass,site4,session_period):

        self.protocol = protocol
        self.hostname = hostname
        self.remote_dir = remote_dir ## setter bellow
        self.remote_fname = remote_fname
        self.sta_user = sta_user
        self.sta_pass = sta_pass  
        self.site4 = site4           
        self.session_period = session_period
        self.translate_dict = None ## setter bellow
        
    def __repr__(self):
        return "session {} on {}".format(self.session_period,self.site4)
        
    #test sur session period !!!!!! sur protocol !!!

    ############ getters and setters 
    @property
    def remote_dir(self):
        return self._remote_dir
    
    @remote_dir.setter
    def remote_dir(self,value):
        if value[0] == "/":
            self._remote_dir = "".join(list(value)[1:])
        else:
            self._remote_dir = value
    
    @property
    def translate_dict(self):
        return self._translate_dict
        
    @translate_dict.setter
    def translate_dict(self,value):
        if not value:
            self._translate_dict = dict()
            self._translate_dict["SITE4"] = self.site4.upper()
        else:
            self._translate_dict = value        
                    
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




# PSA1
protocol = "http"
hostname="http://gps-psa.terrain.ovsg.univ-ag.fr"
remote_dir="download/Internal/%Y%m/"
remote_fname="<SITE4>______%Y%m%d%H%MA.T02"
sta_user=""
sta_pass=""
site4="PSA1"
session_period="1D"

#######' HOUE
protocol = "ftp"
hostname="gps-houe.terrain.ovsg.univ-ag.fr"
remote_dir="/SD Card/Data/HOUE_30s_MDB/<SITE4>/%Y/%m/%d"
remote_fname=""
sta_user="root"
sta_pass="ovsg13;:"
site4="HOUE"
session_period="1D"

#AGAL
protocol = "http"
hostname="http://10.0.76.158"
remote_dir="download/Internal/%Y%m/"
remote_fname=""
sta_user=""
sta_pass=""
site4="AGAL"
session_period="1D"

# ABD0
protocol = "http"
hostname="http://gps-abd.terrain.ovsg.univ-ag.fr/"
remote_dir="download/Internal/%Y%m/"
remote_fname="<SITE4>______%Y%m%d%H%MA.T02"
sta_user=""
sta_pass=""
site4="ABD0"
session_period="1D"

########################################################################

SESS = SessionGnss(protocol = protocol,
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

REQ = RequestGnss(SESS,DR,output_path)

#L = STAT.list_remote_files(DR)
#L = REQ.ask_remote_files()
L = REQ.guess_remote_files()

print("AAAAAA",REQ.req_remote_files)
REQ.download_remote_files()

print(Lguess)
#STAT.download_remote_files(DR,output_path)

