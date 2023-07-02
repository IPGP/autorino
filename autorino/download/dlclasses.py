#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ftplib
import datetime as dt
import pandas as pd
import numpy as np
import os
import dateparser
from autorino import download as ardl

pd.options.mode.chained_assignment = 'warn'

# Create a logger object.
import logging
logger = logging.getLogger(__name__)

def _translator_epoch(path_input,epoch):
    """
    set the correct epoch in path_input string the with the strftime aliases
    https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior
    """
    path_translated = str(path_input)
    path_translated = epoch.strftime(path_translated)
    return path_translated

def _translator_keywords(path_input,translator_dict):
    """
    """
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
    def __init__(self,name,protocol,hostname,remote_dir,
                 remote_fname, sta_user,sta_pass,site,session_period):
        self.name = name
        self.protocol = protocol
        self.hostname = hostname
        self.remote_dir = remote_dir ## setter bellow
        self.remote_fname = remote_fname
        self.sta_user = sta_user
        self.sta_pass = sta_pass  
        self.site = site ## setter bellow
        self.site4 = site  ## setter bellow       
        self.site9 = site   ## setter bellow         
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

    @property
    def site4(self):
        return self._site4
    @site4.setter
    def site4(self,value):
        self._site4 = value[:4]

    @property
    def site9(self):
        return self._site9
    @site9.setter
    def site9(self,value):
        if len(value) == 9:
            self._site9 = value
        elif len(value) == 4:
            self._site9 = value + "00XXX"
        else:
            raise Exception("given site code != 9 or 4 chars.: " + value)
            
    ############ methods
    def _translate_dict_init(self):
        """
        generate the translation dict based on all the SessionGnss 
        object attributes
        
        site code have 2 declinations: 
        <site> (lowercase) and <SITE> (uppercase)
        """
        trsltdict = dict()
        attributes = [a for a in dir(self) if not a.startswith('__') and not callable(getattr(self, a))]
        for a in attributes:
            trsltdict[a] = str(getattr(self, a)).upper()
            if a.lower() in ('site','site4','site9'):
                trsltdict[a.upper()] = str(getattr(self, a)).upper()
                trsltdict[a.lower()] = str(getattr(self, a)).lower()
        return trsltdict


def dateparser_frontend(date_in,tz="UTC"):
    """
    Frontend function to parse a string/datetime 
    to a Pandas Timestamp 
    (standard used for the DownloadGnss object)
    Also apply a timezone (UTC per default)
    
    NB: the rounding will not take place here
    rounding is not a parsing operation
    """
    if type(date_in) is str:
        date_out = pd.Timestamp(dateparser.parse(date_in))
    else:
         date_out = pd.Timestamp(date_in)
    
    if not date_out.tz:
        date_out = pd.Timestamp(date_out, tz=tz)
    
    return date_out
    
def dateround_frontend(date_in,period,round_method="ceil"):
    """    
    Frontend function to round a Pandas Timestamp 
    according to the "ceil", "floor" or "round" approach
    """
    if round_method == "ceil":
        date_out = date_in.ceil(period)
    elif round_method == "floor":
        date_out = date_in.floor(period)        
    elif round_method == "round":
        date_out = date_in.ceil(period)
    else:
        raise Exception
        
    return date_out
        

class EpochRange:
    def __init__(self,epoch1,epoch2,
                 period="01D",
                 round_method="ceil",
                 tz="UTC"):
        self.period = period
        self.round_method = round_method
        self.tz = tz

        self._epoch1_raw = epoch1
        self._epoch2_raw = epoch2
    
        _epoch1tmp = dateparser_frontend(self._epoch1_raw)
        _epoch2tmp = dateparser_frontend(self._epoch2_raw)
        _epoch_min_tmp = np.min((_epoch1tmp,_epoch2tmp))
        _epoch_max_tmp = np.max((_epoch1tmp,_epoch2tmp))
        
        self.epoch_start = _epoch_min_tmp  ### setter bellow
        self.epoch_end   = _epoch_max_tmp  ### setter bellow

    def __repr__(self):
        return "epoch range from {} to {}, period {}".format(self.epoch_start,self.epoch_end,self.period)
    
    ############ getters and setters 
    @property
    def epoch_start(self):
        return self._epoch_start
    @epoch_start.setter
    def epoch_start(self,value):
        self._epoch_start = dateparser_frontend(value,tz=self.tz)
        self._epoch_start = dateround_frontend(self._epoch_start,
                                               self.period,
                                               self.round_method) 
    @property
    def epoch_end(self):
        return self._epoch_end
    @epoch_end.setter
    def epoch_end(self,value):
        self._epoch_end = dateparser_frontend(value,tz=self.tz) 
        self._epoch_end = dateround_frontend(self._epoch_end,
                                             self.period,
                                             self.round_method) 
    ########### methods
    def epoch_range_list(self):
        epochrange=pd.date_range(self.epoch_start,
                                 self.epoch_end,
                                 freq=self.period)
        return list(epochrange)




class WorkflowGnss():
    def __init__(self,session,epoch_range):
        self.session = session
        self.epoch_range = epoch_range ### setter bellow
        self.out_dir = out_dir
        self.table = self._table_init()

class ConvertGnss():
    def __init__():
        pass

class RinexHeaderModGnss():
    def __init__():
        pass


class DownloadGnss():
    def __init__(self,session,epoch_range,out_dir):
        self.session = session
        self.epoch_range = epoch_range ### setter bellow
        self.out_dir = out_dir
        self.table = self._table_init()
        
    ######## getter and setter 
    @property
    def epoch_range(self):
        return self._epoch_range
        
    @epoch_range.setter
    def epoch_range(self,value):
        self._epoch_range = value
        if self._epoch_range.period != self.session.session_period:  
            logger.warn("Session period (%s) != Epoch Range period (%s)",self.session.session_period,self._epoch_range.period)

    ######## internal methods 
    def _table_init(self):
        df = pd.DataFrame(columns=["epoch","fname",
                                   "ok_remote",
                                   "ok_local",
                                   "fpath_remote",
                                   "fpath_local",
                                   "size_local"])
                                   
        df.epoch = self.epoch_range.epoch_range_list()
        df.set_index("epoch",inplace=True,drop=True)
        df = df.where(pd.notnull(df), None)
        
        return df
    
    ########### methods        
    def guess_remote_local_files(self,
                                 guess_remote=True,
                                 guess_local=True):
        """
        Guess the paths and name of the remote files based on the 
        Session and EpochRange attributes of the DownloadGnss
        """
        
        if not self.session.remote_fname:
            logger.warning("generic filename empty for %s, the guessed remote filepaths will be wrong",self.session)

        hostname_use = self.session.hostname
        
        rmot_paths_list = []
        local_paths_list = []
        
        for epoch in self.epoch_range.epoch_range_list():
            ### guess the potential remote files
            if guess_remote:
                rmot_dir_use = str(self.session.remote_dir)
                rmot_fname_use = str(self.session.remote_fname)
                rmot_path_use = os.path.join(hostname_use,
                                             rmot_dir_use,
                                             rmot_fname_use)

                rmot_path_use = translator(rmot_path_use,
                                           epoch,
                                           self.session.translate_dict)
                                           
                rmot_fname_use = os.path.basename(rmot_path_use)
                                           
                rmot_paths_list.append(rmot_path_use)
                self.table.loc[epoch,"fname"]        = rmot_fname_use
                self.table.loc[epoch,"fpath_remote"] = rmot_path_use
                logger.debug("remote file guessed: %s",rmot_path_use)

            ### guess the potential local files
            if guess_local:
                local_dir_use = str(self.out_dir)
                local_fname_use = str(self.session.remote_fname)
                local_path_use = os.path.join(local_dir_use,
                                              local_fname_use)

                local_path_use = translator(local_path_use,
                                            epoch,
                                            self.session.translate_dict)
                                            
                local_fname_use = os.path.basename(local_path_use)
                                           
                local_paths_list.append(local_path_use)
                self.table.loc[epoch,"fname"]       = local_fname_use
                self.table.loc[epoch,"fpath_local"] = local_path_use
                logger.debug("local file guessed: %s",local_path_use)
      
        rmot_paths_list = sorted(list(set(rmot_paths_list)))
            
        logger.info("nbr remote files guessed: %s",len(rmot_paths_list))
        logger.info("nbr local files guessed: %s",len(local_paths_list))

        return rmot_paths_list, local_paths_list
        
        
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
        
    def check_local_files(self):
        """
        check the existence of the local files, and set the corresponding
        booleans in the ok_local column
        """
        
        local_files_list = []
        
        for epoch,local_file in self.table.fpath_local.items():
            if os.path.exists(local_file) and os.path.getsize(local_file) > 0:
                self.table.ok_local.loc[epoch] = True
                self.table.size_local.loc[epoch] = os.path.getsize(local_file)

                local_files_list.append(local_file)
            else:
                self.table.ok_local.loc[epoch] = False
                
        return local_files_list
        
    def invalidate_small_local_files(self,threshold=.80):
        """
        if the local file is smaller than threshold * median 
        of the considered local files in the request table
        the ok_local boolean is set at False, and the local file 
        is redownloaded
        
        check_local_files must be launched 1st
        """
        
        med = self.table.size_local.median(skipna=True)
        valid_bool = threshold * med < self.table.size_local
        self.table.loc[:,"ok_local"] = valid_bool
        invalid_local_files_list = list(self.table.fpath_local[valid_bool])

        return invalid_local_files_list


    def download_remote_files(self,force_download=False):
        """
        will download locally the files which have been identified by 
        the guess_remote_files method
        
        exploits the fname_remote column of the DownloadGnss.table
        attribute
        """
        download_files_list = []
                
        for (epoch,rmot_file),(_,local_file) in zip(self.table.fpath_remote.items(),
                                                    self.table.fpath_local.items()):
            ###### check if the file exists locally
            if self.table.loc[epoch,'ok_local'] == True and not force_download:
                 logger.info("%s already exists locally, skip",os.path.basename(local_file))
                 continue

            ###### use the guessed local file as destination or the generic directory                
            if not local_file: #### the local file has not been guessed
                outdir_use = str(self.out_dir)
                outdir_use = translator(outdir_use,
                                        epoch,
                                        self.session.translate_dict)
            else: #### the local file has been guessed before
                outdir_use = os.path.dirname(local_file)
            
            ###### create the directory if it does not exists
            if not os.path.exists(outdir_use):
                os.makedirs(outdir_use)
            
            ###### download the file            
            if not self.session.protocol in ("ftp","http"):
                logger.error("wrong protocol")
                raise Exception
            elif self.session.protocol == "http":
                try:
                    file_dl = ardl.download_file_http(rmot_file,
                                                      outdir_use)
                    dl_ok = True
                except Exception as e:
                    logger.error("HTTP download error: %s",str(e))
                    dl_ok = False
                    
            elif self.session.protocol == "ftp":
                try:
                    file_dl = ardl.download_file_ftp(rmot_file,
                                                     outdir_use,
                                                     self.session.sta_user,
                                                     self.session.sta_pass)
                    dl_ok = True
                except ftplib.error_perm as e:
                    logger.error("FTP download error: %s",str(e))
                    dl_ok = False
                    
            else: ### this case should never happen since there is a protocol test at the begining
                pass

            ###### store the results in the table
            if dl_ok:
                download_files_list.append(file_dl)
                self.table.loc[epoch,"ok_local"] = True
                self.table.loc[epoch,"fpath_local"] = file_dl
            else:
                self.table.loc[epoch,"ok_local"] = False
                
        return download_files_list
