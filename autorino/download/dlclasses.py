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


def _translator_epoch(path_input,epoch):
    path_translated = str(path_input)
    path_translated = epoch.strftime(path_translated)
    return path_translated

def _translator_keywords(path_input,translator_dict):
    path_translated = str(path_input)
    for k,v in translator_dict.items():
        path_translated = path_translated.replace("<"+k+">",v)
    return path_translated
    
def translator(path_input,epoch=None,translator_dict=None):
    path_translated = str(path_input)
    if epoch:
        path_translated = _translator_epoch(path_translated,epoch)
    if translator_dict:
        path_translated = _translator_keywords(path_translated,translator_dict)
    return path_translated
    
    

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
        self.translate_dict = self._translate_dict_init()
        
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
    
    def _translate_dict_init(self):
        """
        generate the translation dict based on all the SessionGnss 
        object attributes
        """
        trsltdict = dict()
        attributes = [a for a in dir(self) if not a.startswith('__') and not callable(getattr(self, a))]
        for a in attributes:
            trsltdict[a.upper()] = str(getattr(self, a)).upper()
            trsltdict[a.lower()] = str(getattr(self, a)).lower()
        return trsltdict

class EpochRange:
    def __init__(self,epoch1,epoch2,period="01D",round_method="ceil"):
        self.period = period
        self.round_method = round_method
        self.epoch_start_raw = np.min((epoch1,epoch2))
        self.epoch_end_raw = np.max((epoch1,epoch2))
        self.epoch_start = self.epoch_start_raw  ### setter bellow
        self.epoch_end = self.epoch_end_raw      ### setter bellow

    def __repr__(self):
        return "epoch range from {} to {}, period {}".format(self.epoch_start,self.epoch_end,self.period)
    
    ############ getters and setters 
    @property
    def epoch_start(self):
        return self._epoch_start
        
    @epoch_start.setter
    def epoch_start(self,value):
        self._epoch_start = pd.Timestamp(value).ceil(self.period)
    
    @property
    def epoch_end(self):
        return self._epoch_end
        
    @epoch_end.setter
    def epoch_end(self,value):
        self._epoch_end = pd.Timestamp(value).ceil(self.period)
        
    ########### methods
    def epoch_range_list(self):
        epochrange=pd.date_range(self.epoch_start,
                                 self.epoch_end,
                                 freq=self.period)
        return list(epochrange)
    
class RequestGnss():
    def __init__(self,session,epoch_range,out_dir):
        self.session = session
        self.epoch_range = epoch_range ### setter bellow
        self.out_dir = out_dir
        self.req_table = self._req_table_init()
        
    @property
    def epoch_range(self):
        return self._epoch_range
        
    @epoch_range.setter
    def epoch_range(self,value):
        self._epoch_range = value
        if self._epoch_range.period != self.session.session_period:  
            logger.warn("Session period (%s) != Epoch Range period (%s)",self.session.session_period,self._epoch_range.period)

    def _req_table_init(self):
        df = pd.DataFrame(data=None,columns=["epoch","fname",
                                             "ok_remote",
                                             "ok_local",
                                             "fpath_remote",
                                             "fpath_local"])
                                   
        df.epoch = self.epoch_range.epoch_range_list()
        df.set_index("epoch",inplace=True,drop=True)
        return df
    
    ########### methods        
    def check_local_files(self):
        """
        """
        return rmot_paths_list
        
        
    def guess_remote_local_files(self):
        """
        Guess the paths and name of the remote files based on the 
        Session and EpochRange attributes of the GnssRequest
        """
        
        if not self.session.remote_fname:
            logger.warning("generic filename empty for %s, the guessed remote filepaths will be wrong",self.session)

        hostname_use = self.session.hostname
        
        rmot_paths_list = []
        
        
        
        
        
        
        
        for epoch in self.epoch_range.epoch_range_list():
            ### guess the potential directories
            rmot_dir_use = str(self.session.remote_dir)
            rmot_dir_use = translator(rmot_dir_use,
                                      epoch,
                                      self.session.translate_dict)
                                                    
            ### guess the potential filenames
            rmot_fname_use = str(self.session.remote_fname)
            
            rmot_fname_use = translator(rmot_fname_use,
                                        epoch,
                                        self.session.translate_dict)

            rmot_path_use = os.path.join(hostname_use,
                                         rmot_dir_use,
                                         rmot_fname_use)

            rmot_paths_list.append(rmot_path_use)
            self.req_table.loc[epoch,"fname"]        = rmot_fname_use
            self.req_table.loc[epoch,"fpath_remote"] = rmot_path_use
                        
            logger.debug("remote file guessed: %s",rmot_path_use)
        
        rmot_paths_list = sorted(list(set(rmot_paths_list)))
            
        logger.info("nbr remote files guessed: %s",len(rmot_paths_list))
        return rmot_paths_list
        
        
    def _guess_remote_directories(self):
        """
        this method is specific for ask_remote_files
        guessing the directories is different than guessing the files:
        * no hostname
        * no filename (obviously)
        """
        rmot_dir_list = []
        for epoch in self.epoch_range.epoch_range_list():
            rmot_dir_use = str(self.session.remote_dir)
            rmot_dir_use = translator(rmot_dir_use,epoch,
                                      self.session.translate_dict)
            rmot_dir_list.append(rmot_dir_use)
            
        rmot_dir_list = sorted(list(set(rmot_dir_list)))
                    
        return rmot_dir_list
    
    def ask_remote_files(self):
        rmot_dir_list = self._guess_remote_directories()
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
        
        logger.info("nbr remote files found on rec: %s",len(rmot_files_list))
        return rmot_files_list

    def download_remote_files(self):
        """
        will download locally the files which have been identified by 
        the guess_remote_files method
        
        exploits the fname_remote column of the RequestGnss.req_table
        attribute
        """
        download_files_list = []
                
        for epoch,rmot_file in self.req_table.fpath_remote.items():
            
            outdir_use = self.out_dir
            
            if  self.session.protocol == "http":
                file_dl = ardl.download_file_http(rmot_file,
                                                  outdir_use)
                download_files_list.append(file_dl)
                self.req_table.fpath_local.loc[epoch] = file_dl

            elif self.session.protocol == "ftp":
                file_dl = ardl.download_file_ftp(rmot_file,
                                                 outdir_use,
                                                 self.session.sta_user,
                                                 self.session.sta_pass)
                download_files_list.append(file_dl)
                self.req_table.fpath_local.loc[epoch] = file_dl

            else:
                logger.error("wrong protocol")
                
        self.req_local_files = download_files_list
        
        return download_files_list


