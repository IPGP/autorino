#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  8 16:53:51 2024

@author: psakicki
"""

#### Import the logger
import logging
import pandas as pd
import numpy as np
import os
import re
import copy
 
from geodezyx import utils

import autorino.epochrange as aroepo

logger = logging.getLogger(__name__)
logger.setLevel("INFO")

class WorkflowGnss():
    
    def __init__(self,session,epoch_range,out_dir):
        self.session = session
        self.epoch_range = epoch_range ### setter bellow
        self.out_dir = out_dir
        self.tmp_dir = session.tmp_dir
        self._table_init()
        
    def __repr__(self):
        name = type(self).__name__
        out = "{} {}/{}".format(name, self.session.site, self.epoch_range)
        return out
    
    ######## getter and setter 
    @property
    def epoch_range(self):
        return self._epoch_range
        
    @epoch_range.setter
    def epoch_range(self,value):
        self._epoch_range = value
        if self._epoch_range.period != self.session.session_period:  
            logger.warn("Session period (%s) ≠ Epoch Range period (%s)",
            self.session.session_period,self._epoch_range.period)

    @property
    def table(self):
        return self._table
        
    @table.setter
    def table(self,value):
        self._table = value
        #### designed for future safety tests
        
    def _table_init(self,
                    table_cols=['fname',
                                'site',
                                'epoch_srt',
                                'epoch_end',
                                'ok_inp',
                                'ok_out',
                                'fpath_inp',
                                'fpath_out',
                                'size_inp',
                                'size_out',
                                'note'],
                    init_epoch=True):
                
        df = pd.DataFrame([], columns=table_cols)
        
        if init_epoch:
            df['epoch_srt'] = self.epoch_range.epoch_range_list()
            df['epoch_end'] = self.epoch_range.epoch_range_list(end_bound=True)   
            
            df['site'] = self.session.site 
        
        self.table = df
        return df
        
    ######## internal methods 
    
    def duplicate(self):
        """
        return a duplicate (deep copy) of the current object
        """
        return copy.deepcopy(self)
    
    
    def update_epoch_range_from_table(self):
        epomin = self.table['epoch_srt'].min()
        epomax = self.table['epoch_srt'].max()
        
        self.epoch_range.epoch1 = epomin
        self.epoch_range.epoch1 = epomax
        
        tdelta_arr = self.table['epoch_srt'].diff().dropna().unique()
        
        if len(tdelta_arr) > 1:
            logger.warn("the period spacing of %s is not uniform".self)
            ##### be sure to keep the 1st one!!!
        
        period_new = aroepo.timedelta2freqency_alias(tdelta_arr[0])
        self.epoch_range.period = period_new
        
        logger.info("new %s",self.epoch_range)
        
        
        


# _______    _     _                                                                    _   
#|__   __|  | |   | |                                                                  | |  
#   | | __ _| |__ | | ___   _ __ ___   __ _ _ __   __ _  __ _  ___ _ __ ___   ___ _ __ | |_ 
#   | |/ _` | '_ \| |/ _ \ | '_ ` _ \ / _` | '_ \ / _` |/ _` |/ _ \ '_ ` _ \ / _ \ '_ \| __|
#   | | (_| | |_) | |  __/ | | | | | | (_| | | | | (_| | (_| |  __/ | | | | |  __/ | | | |_ 
#   |_|\__,_|_.__/|_|\___| |_| |_| |_|\__,_|_| |_|\__,_|\__, |\___|_| |_| |_|\___|_| |_|\__|
#                                                        __/ |                              
#                                                       |___/     
  
        
    def print_table(self,
                    no_print=False,
                    no_return=True,
                    max_colwidth=33):
        
        def _shrink_str(str_inp,maxlen=max_colwidth):
            if len(str_inp) <= maxlen:
                return str_inp
            else:
                halflen = int((maxlen / 2)  - 1)
                str_out = str_inp[:halflen] + '..' + str_inp[-halflen:]
                return str_out
        
        form = dict()
        form['fraw'] = _shrink_str
        form['fpath_inp'] = _shrink_str
        form['fpath_out'] = _shrink_str
        
        form['epoch_srt'] = lambda t: t.strftime("%y-%m-%d %H:%M:%S")
        form['epoch_end'] = lambda t: t.strftime("%y-%m-%d %H:%M:%S")

        str_out = self.table.to_string(max_colwidth=max_colwidth+1,
                                       formatters=form)
                                       ### add +1 in max_colwidth for safety                                    
        if not no_print:
            ### print it in the logger (if silent , just return it)
            name = type(self).__name__
            logger.info("%s %s/%s\n%s",name,
                                       self.session.site,
                                       self.epoch_range,
                                       str_out)
        if no_return:
            return None
        else:
            return output

        
        
    def load_table_from_filelist(self,
                                 input_files,
                                 inp_regex=".*",
                                 reset_table=True):
        if reset_table:
            self._table_init(init_epoch=False)
        
        flist = input_list_reader(input_files,
                                  inp_regex)
                
        self.table['fpath_inp'] = flist
        self.table['ok_inp'] = self.table['fpath_inp'].apply(os.path.isfile)
        
        return flist
        
    
    def load_table_from_prev_step_table(self,
                                        input_table,
                                        reset_table=True):
        if reset_table:
            self._table_init(init_epoch=False)
                          
        self.table['fpath_inp'] = input_table['fpath_out'].values
        self.table['size_inp'] = input_table['size_out'].values
        self.table['fname'] = self.table['fpath_inp'].apply(os.path.basename)
        self.table['site'] = input_table['site'].values
        self.table['epoch_srt'] = input_table['epoch_srt'].values
        self.table['epoch_end'] = input_table['epoch_end'].values
        self.table['ok_inp'] = self.table['fpath_inp'].apply(os.path.isfile)
        
        return None
    
    def guess_local_files(self,
                          guess_remote=True,
                          guess_local=True):
        """
        Guess the paths and name of the local files based on the 
        Session and EpochRange attributes of the DownloadGnss
        
        see also method guess_remote_files(), 
        a specific method for DownloadGnss objects 
        """
        
        if not self.session.remote_fname:
            logger.warning("generic filename empty for %s, the guessed remote filepaths will be wrong",self.session)
        
        rmot_paths_list = []
        local_paths_list = []
        
        for epoch in self.epoch_range.epoch_range_list():

        ### guess the potential local files
            local_dir_use = str(self.out_dir)
            local_fname_use = str(self.session.remote_fname)
            local_path_use = os.path.join(local_dir_use,
                                          local_fname_use)

            local_path_use = translator(local_path_use,
                                        epoch,
                                        self.session.translate_dict)
                                        
            local_fname_use = os.path.basename(local_path_use)
                                       
            local_paths_list.append(local_path_use)

            iepoch = self.table[self.table['epoch_srt'] == epoch].index

            self.table.loc[iepoch,'fname']       = local_fname_use
            self.table.loc[iepoch,'fpath_out'] = local_path_use
            logger.debug("local file guessed: %s",local_path_use)
  
        rmot_paths_list = sorted(list(set(rmot_paths_list)))
            
        logger.info("nbr local files guessed: %s",len(local_paths_list))

        return local_paths_list
        

#  ______ _ _ _              _        _     _      
# |  ____(_) | |            | |      | |   | |     
# | |__   _| | |_ ___ _ __  | |_ __ _| |__ | | ___ 
# |  __| | | | __/ _ \ '__| | __/ _` | '_ \| |/ _ \
# | |    | | | ||  __/ |    | || (_| | |_) | |  __/
# |_|    |_|_|\__\___|_|     \__\__,_|_.__/|_|\___|
                                                
           
    def filter_bad_keywords(self,keywords_path_excl):
        """
        Filter a list of raw files if the full path contains certain keywords
        
        modify the boolean "ok_inp" of the object's table
        returns the filtered raw files in a list
        """
        flist_out = []
        ok_inp_bool_stk = []
        nfil = 0 
        for irow,row in self.table.iterrows():
            f = row['fname']
            boolbad = utils.patterns_in_string_checker(f,*keywords_path_excl)
            if boolbad:
                self.table.iloc[irow,'ok_inp'] = False
                logger.debug("file filtered, contains an excluded keyword: %s",
                             f)
                nfil += 1
            else:
                if not row.ok_inp: ### ok_inp is already false
                    ok_inp_bool_stk.append(False)
                else:
                    ok_inp_bool_stk.append(True)
                    flist_out.append(f)
                    
        ### final replace of ok init
        self.table['ok_inp'] = ok_inp_bool_stk
                    
        logger.info("%6i files filtered, their paths contain bad keywords",
                    nfil)
        return flist_out
    
    
    def filter_year_min_max(self,
                            year_min=1980,
                            year_max=2099,
                            year_in_inp_path=None):
        """
        Filter a list of raw files if they are not in a year range
        it is the year in the file path which is tested
        
        year_in_inp_path is the position of the year in the absolute path
        e.g.
        if the absolute path is:
        /home/user/input_data/raw/2011/176/PSA1201106250000a.T00
        year_in_inp_path is 4
        
        if no year_in_inp_path provided, a regex search is performed
        (more versatile, but less robust)
        
        
        year min and year max are included in the range
        
        modify the boolean "ok_inp" of the object's table
        returns the filtered raw files in a list
        """
        flist_out = []
        #nfil = 0 
        
        ok_inp_bool_stk = []
        
        def _year_detect(fpath_inp,year_in_inp_path=None):
            try:
                if year_in_inp_path:
                    year_folder = int(fpath_inp.split("/")[year_in_inp_path])
                else:
                    rgx = re.search("\/(19|20)[0-9]{2}\/",fpath_inp)
                    year_folder = int(rgx.group()[1:-1])         
                return year_folder
            except:
                logger.warning("unable to get the year in path: %s",
                               fpath_inp)
                return np.nan
            
        years = self.table['fraw'].apply(_year_detect,args=(year_in_inp_path,))
        
        bool_out_range = (years < year_min) | (years > year_max)
        bool_in_range = np.logical_not(bool_out_range)
        
        #############################
    
        ok_inp_bool_stk = bool_in_range & self.table['ok_inp']
        nfil_total = sum(bool_out_range)
        ### logical inhibition a.\overline{b}
        nfil_spec = sum(np.logical_and(bool_out_range, self.table['ok_inp']))
        
        ### final replace of ok init
        self.table['ok_inp'] = ok_inp_bool_stk

        logger.info("%6i/%6i files filtered (total/specific) not in the year min/max range (%4i/%4i)",
                    nfil_total, nfil_spec ,year_min,year_max)

        return flist_out 
    

    
    def filter_filelist(self,filelist_exclu_inp,
                              message_manu_exclu=False):
        """
        Filter a list of raw files if they are present in a text file list 
        e.g. an OK log or manual exclusion list
        
        modify the boolean "ok_inp" of the object's table
        returns the filtered raw files in a list
        """
        
        flist_exclu = input_list_reader(filelist_exclu_inp)
        
        flist_out = []
        ok_inp_bool_stk = []
        
        nfil = 0 
        for irow,row in self.table.iterrows():
            f = row.fraw
            if f in flist_exclu:
                nfil += 1
                ok_inp_bool_stk.append(False)
                if not message_manu_exclu:
                    logger.debug("file filtered, was OK during a previous run (legacy simple list): %s",f)
                else:
                    logger.debug("file filtered manually in the exclusion list: %s",f)
            else:
                if not row.ok_inp: ### ok_inp is already false
                    ok_inp_bool_stk.append(False)
                else:
                    ok_inp_bool_stk.append(True)
                    flist_out.append(f)
            
        if not message_manu_exclu:
            logger.info("%6i files filtered, were OK during a previous run (legacy simple OK list)", nfil)
        else:
            logger.info("%6i files manually filtered in the exclusion list,", nfil)
            
        ### final replace of ok init
        self.table['ok_inp'] = ok_inp_bool_stk
    
        return flist_out    
    
    def filter_previous_tables(self,
                               DF_prev_tab):
        """
        Filter a list of raw files if they are present in previous 
        conversion tables stored as log
        
        modify the boolean "ok_inp" of the object's table
        returns the filtered raw files in a list
        """
        
        col_ok_names = ["ok_inp","ok_conv","ok_rnxmod"]
        
        #### previous files when everthing was ok
        prev_bool_ok = DF_prev_tab[col_ok_names].apply(np.logical_and.reduce,
                                                       axis=1)
                
        prev_files_ok = DF_prev_tab[prev_bool_ok].fraw
        
        ### current files which have been already OK and which have already 
        ### ok_inp == False
        ### here the boolean value are inverted compared to the table:
        # True = skip me / False = keep me 
        # a logical not inverts everything at the end
        curr_files_ok_prev = self.table['fraw'].isin(prev_files_ok)
        curr_files_off_already = np.logical_not(self.table['ok_inp'])
        
        curr_files_skip = np.logical_or(curr_files_ok_prev,
                                        curr_files_off_already)

        self.table['ok_inp'] = np.logical_not(curr_files_skip)
        
        logger.info("%6i files filtered, were OK during a previous run (table list)",
                    curr_files_ok_prev.sum())
        
        flist_out = list(self.table['fraw',self.table['ok_inp']])

        return flist_out
    
    def filter_purge(self,col='ok_inp',inplace=False):
        """
        filter the table according to a "ok" column
        i.e. remove all the values with a False values
        """
        if inplace:
            self.table = self.table[self.table[col]]
            out = list(self.table['fraw'])
        else:
            out = self.table[self.table[col]]
        return out
    
    
    def group_epochs(self,
                     period = '1d',
                     rolling_period=False,
                     rolling_ref=-1,
                     round_method = 'floor'):
        
        epoch_rnd = aroepo.round_epochs(self.table['epoch_srt'],
                                        period=period,
                                        rolling_period=rolling_period,
                                        rolling_ref=rolling_ref,
                                        round_method=round_method)
             
        self.table['epoch_rnd'] = epoch_rnd
        
        grps = self.table.groupby('epoch_rnd')
        
        wrkflw_lis_out = []
        
        for tgrp, tabgrp in grps:
            wrkflw = self.duplicate()
            tabgrp_bis = tabgrp.drop('epoch_rnd',axis=1)
            wrkflw.table = tabgrp_bis
            wrkflw_lis_out.append(wrkflw)
    
        return wrkflw_lis_out   

    
        

        
        
        
        
        
        
        
            
        
        
        
        

#  __  __ _               __                  _   _                  
# |  \/  (_)             / _|                | | (_)                 
# | \  / |_ ___  ___    | |_ _   _ _ __   ___| |_ _  ___  _ __  ___  
# | |\/| | / __|/ __|   |  _| | | | '_ \ / __| __| |/ _ \| '_ \/ __| 
# | |  | | \__ \ (__ _  | | | |_| | | | | (__| |_| | (_) | | | \__ \ 
# |_|  |_|_|___/\___(_) |_|  \__,_|_| |_|\___|\__|_|\___/|_| |_|___/ 
                                                                 

def _translator_epoch(path_inp,epoch_inp):
    """
    set the correct epoch in path_input string the with the strftime aliases
    https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior
    """
    path_translated = str(path_inp)
    path_translated = epoch_inp.strftime(path_translated)
    return path_translated

def _translator_keywords(path_inp,translator_dict):
    """
    """
    path_translated = str(path_inp)
    for k,v in translator_dict.items():
        path_translated = path_translated.replace("<"+k+">",v)
    return path_translated
    
def translator(path_inp,epoch_inp=None,translator_dict=None):
    path_translated = str(path_inp)
    if epoch_inp:
        path_translated = _translator_epoch(path_translated,epoch_inp)
    if translator_dict:
        path_translated = _translator_keywords(path_translated,translator_dict)
    return path_translated


def input_list_reader(inp_fil,inp_regex=".*"):
    """
    Handles mutiples types of input lists (in a general sense)  
    and returns a python list of the input
    
    inp_fil can be:
        * a python list (then nothing is done)
        * a text file path containing a list of files 
        (readed as a python list)
        * a tuple containing several text files path 
        (recursive version of the previous point)
        * a directory path (all the files matching inp_regex are readed)
    """

    if not inp_fil:
        flist  = []
    elif type(inp_fil) is tuple and os.path.isfile(inp_fil[0]):
        flist = list(np.hstack([open(f,"r+").readlines() for f in inp_fil]))
        flist = [f.strip() for f in flist]
    elif type(inp_fil) is list:
        flist = inp_fil
    elif os.path.isfile(inp_fil):
        flist = open(inp_fil,"r+").readlines()
        flist = [f.strip() for f in flist]
    elif os.path.isdir(inp_fil):
        flist = utils.find_recursive(inp_fil,
                                     inp_regex,
                                     case_sensitive=False)
    else:
        flist = []
        logger.warning("the filelist is empty") 
        
    if inp_regex != ".*":
        flist = [f for f in flist if re.match(inp_regex, f)]
        
    return flist
