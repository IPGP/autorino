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

#import autorino.epochrange as aroepo
import autorino.general as arogen
from autorino import logconfig

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

class StepGnss():
    
    def __init__(self,
                 out_dir,tmp_dir,log_dir,
                 epoch_range,
                 site=None,
                 session=None,
                 site_id=None):
        
        self.out_dir = out_dir
        self.tmp_dir = tmp_dir
        self.log_dir = log_dir
        self.epoch_range = epoch_range ### setter bellow
        
        self._init_site(site)
        self._init_session(session)
        self._init_site_id(site_id)
        self._init_table()
        
        self.translate_dict = self._set_translate_dict()

        self.set_logfile()
        
    def __repr__(self):
        name = type(self).__name__
        out = "{} {}/{}".format(name,
                                self.site_id,
                                self.epoch_range)
        return out
    
    ######## getter and setter 
    #### site_id
    @property
    def site_id(self):
        return self._site_id
    @site_id.setter
    def site_id(self,value):
        self._site_id = value

    @property
    def site_id4(self):
        return self._site_id[:4]
    
    # @site_id4.setter
    # def site_id4(self,value):
    #     self._site_id4 = value[:4]

    @property
    def site_id9(self):
        if len(self._site_id) == 9:
            return self._site_id
        elif len(self._site_id) == 4:
            return self._site_id + "00XXX"
        else:
            return self._site_id[:4]  + "00XXX"
        
        
    #     return self._site_id9
    # @site_id9.setter
    # def site_id9(self,value):
    #     if len(value) == 9:
    #         self._site_id9 = value
    #     elif len(value) == 4:
    #         self._site_id9 = value + "00XXX"
    #     else:
    #         raise Exception("given site code != 9 or 4 chars.: " + value)
    
    
    #### epoch_range
    @property
    def epoch_range(self):
        return self._epoch_range
        
    @epoch_range.setter
    def epoch_range(self,value):
        self._epoch_range = value
        ## this test becones useless after session class suppression (240126)
        # if self._epoch_range.period != self.session.session_period:  
        #     logger.warn("Session period (%s) ≠ Epoch Range period (%s)",
        #     self.session.session_period,self._epoch_range.period)
    
    #### table
    @property
    def table(self):
        return self._table
        
    @table.setter
    def table(self,value):
        self._table = value
        #### designed for future safety tests

    def _init_table(self,
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
            
            df['site'] = self.site_id
        
        self.table = df
        return df
    
    def _init_site(self,site):
        """
        if a site dict is not given, create a dummy one
        """
        
        if not site:
            logger.warn('no site dict given, a dummy one will be created')
            self.site = create_dummy_site_dic()
        else:
            self.site = site

    def _init_session(self,session):
        """
        if a session dict is not given, create a dummy one
        """
        
        if not session:
            logger.warn('no session dict given, a dummy one will be created')
            self.session = create_dummy_session_dic()
        else:
            self.session = session

    def _init_site_id(self,site_id):
        """
        if a site id is not explicitely given, take the one from the site dict 
        A dummy site dict  will be created in the worst case, ensuring that 
        site_id will be always initialized
        """
        if not site_id:
            self.site_id = self.site['site_id']
        else:
            self.site_id = site_id


    def _set_translate_dict(self):
        """
        generate the translation dict based on the access and session dicts 
        object attributes + site id
        
        site code have 2x3 declinations: 
        <site_id(4|9|)> (lowercase) and <SITE_ID(4|9|)> (uppercase)
        """
        trsltdict = dict()
        
        for dic in (self.site ,
                    self.session):
            for k,v in dic.items():
                trsltdict[k] = v
                
        ### site have a specific loop
        for s in ('site_id','site_id4','site_id9'):
            trsltdict[s.upper()] = str(getattr(self,s)).upper()
            trsltdict[s.lower()] = str(getattr(self,s)).lower()        
                
        return trsltdict

        

 #   _____                           _                  _   _               _     
 #  / ____|                         | |                | | | |             | |    
 # | |  __  ___ _ __   ___ _ __ __ _| |  _ __ ___   ___| |_| |__   ___   __| |___ 
 # | | |_ |/ _ \ '_ \ / _ \ '__/ _` | | | '_ ` _ \ / _ \ __| '_ \ / _ \ / _` / __|
 # | |__| |  __/ | | |  __/ | | (_| | | | | | | | |  __/ |_| | | | (_) | (_| \__ \
 #  \_____|\___|_| |_|\___|_|  \__,_|_| |_| |_| |_|\___|\__|_| |_|\___/ \__,_|___/
                                                                                                                                                          
    
    def copy(self):
        """
        return a duplicate (deep copy) of the current object
        """
        return copy.deepcopy(self)
    
    
    def update_epoch_range_from_table(self,
                                      column='epoch_srt'):
        """
        update the EpochRange of the StepGnss object with 
        the min/max of the epochs in the object's table
        """
        epomin = self.table[column].min()
        epomax = self.table[column].max()
        
        self.epoch_range.epoch1 = epomin
        self.epoch_range.epoch1 = epomax
        
        tdelta_arr = self.table[column].diff().dropna().unique()
        
        if len(tdelta_arr) > 1:
            logger.warn("the period spacing of %s is not uniform".self)
            ##### be sure to keep the 1st one!!!
        
        period_new = arogen.timedelta2freqency_alias(tdelta_arr[0])
        self.epoch_range.period = period_new
        
        logger.info("new %s",self.epoch_range)



 #  _                       _             
 # | |                     (_)            
 # | |     ___   __ _  __ _ _ _ __   __ _ 
 # | |    / _ \ / _` |/ _` | | '_ \ / _` |
 # | |___| (_) | (_| | (_| | | | | | (_| |
 # |______\___/ \__, |\__, |_|_| |_|\__, |
 #               __/ | __/ |         __/ |
 #              |___/ |___/         |___/
              

    def set_logfile(self,
                    log_dir_inp=None,
                    step_suffix=''):
        """
        set logging in a file 
        """
                        
        if not log_dir_inp:
            log_dir = self.log_dir
        else:
            log_dir = log_dir_inp
            
            
        log_dir_use = arogen.translator(log_dir,
                                        None, 
                                        self.translate_dict)
        
        _logger = logging.getLogger('autorino')
        
        ts = utils.get_timestamp()
        log_name = "_".join((ts , ".log"))
        log_path = os.path.join(log_dir_use,log_name)

        log_cfg_dic = logconfig.logconfig.log_config_dict
        fmt_dic = log_cfg_dic['formatters']['fmtgzyx_nocolor']

        logfile_handler = logging.FileHandler(log_path)

        fileformatter = logging.Formatter(**fmt_dic)
        
        logfile_handler.setFormatter(fileformatter)
        logfile_handler.setLevel('DEBUG')
        
        
        #### the root logger 
        # https://stackoverflow.com/questions/48712206/what-is-the-name-of-pythons-root-logger
        #### the heritage for loggers
        # https://stackoverflow.com/questions/29069655/python-logging-with-a-common-logger-class-mixin-and-class-inheritance
        _logger.addHandler(logfile_handler)
        
        return logfile_handler
    
    def set_table_log(self,
                      out_dir=None, 
                      step_suffix=''):
        if not out_dir:
            out_dir=self.tmp_dir
                          
        ts = utils.get_timestamp()
        talo_name = "_".join((ts , step_suffix , "table.log"))
        talo_path = os.path.join(out_dir,talo_name)
        
        ### initalize with a void table
        talo_df_void = pd.DataFrame([], columns=self.table.columns)
        talo_df_void.to_csv(talo_path,mode="w",index=False)
        
        self.table_log_path = talo_path
        
        return talo_path
    
    def write_in_table_log(self,row_in):    
        pd.DataFrame(row_in).T.to_csv(self.table_log_path,
                                      mode='a',
                                      index=False,
                                      header=False) 
        return None
    


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
                                       self.site_id,
                                       self.epoch_range,
                                       str_out)
        if no_return:
            return None
        else:
            return str_out
            

    def load_table_from_filelist(self,
                                 input_files,
                                 inp_regex=".*",
                                 reset_table=True):
        if reset_table:
            self._init_table(init_epoch=False)
        
        flist = input_list_reader(input_files,
                                  inp_regex)
                
        self.table['fpath_inp'] = flist
        self.table['ok_inp'] = self.table['fpath_inp'].apply(os.path.isfile)
        
        return flist
        
    
    def load_table_from_prev_step_table(self,
                                        input_table,
                                        reset_table=True):
        if reset_table:
            self._init_table(init_epoch=False)
                          
        self.table['fpath_inp'] = input_table['fpath_out'].values
        self.table['size_inp'] = input_table['size_out'].values
        self.table['fname'] = self.table['fpath_inp'].apply(os.path.basename)
        self.table['site'] = input_table['site'].values
        self.table['epoch_srt'] = input_table['epoch_srt'].values
        self.table['epoch_end'] = input_table['epoch_end'].values
        self.table['ok_inp'] = self.table['fpath_inp'].apply(os.path.isfile)
        
        return None
    
    def guess_local_files(self,
                          guess_local=True):
        """
        Guess the paths and name of the local files based on the 
        Session and EpochRange attributes of the DownloadGnss
        
        see also method guess_remote_files(), 
        a specific method for DownloadGnss objects 
        """
        
        rmot_paths_list = []
        local_paths_list = []
        
        for epoch in self.epoch_range.epoch_range_list():

            ### guess the potential local files
            local_dir_use = str(self.out_dir)
            local_fname_use = str(self.remote_fname)
            local_path_use = os.path.join(local_dir_use,
                                          local_fname_use)

            local_path_use = arogen.translator(local_path_use,
                                               epoch,
                                               self.translate_dict)
                                        
            local_fname_use = os.path.basename(local_path_use)
                                       
            local_paths_list.append(local_path_use)

            iepoch = self.table[self.table['epoch_srt'] == epoch].index

            self.table.loc[iepoch,'fname']     = local_fname_use
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
        
        epoch_rnd = arogen.round_epochs(self.table['epoch_srt'],
                                        period=period,
                                        rolling_period=rolling_period,
                                        rolling_ref=rolling_ref,
                                        round_method=round_method)
             
        self.table['epoch_rnd'] = epoch_rnd
        
        grps = self.table.groupby('epoch_rnd')
        
        wrkflw_lis_out = []
        
        for tgrp, tabgrp in grps:
            wrkflw = self.copy()
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
                                                                 

def create_dummy_site_dic():
    d = dict()   
    
    d['name'] = 'RVAG'
    d['id'] = 'RVAG00REU'
    d['domes'] = '00000X000'
    d['sitelog_path'] = '/null'
    d['position_xyz'] = (1,2,3)
    
    return d


def create_dummy_session_dic():
    
    d = dict()
    
    d['name'] = 'NA' 
    d['data_frequency'] =    "30S" 
    d['tmp_dir_parent'] =    '/home/sysop/workflow_tests/temp'
    d['tmp_dir_structure'] = '<site_id9>/%Y/%j'  
    d['log_parent_dir'] =  '/home/sysop/workflow_tests/log'
    d['log_dir_structure'] = '<site_id9>/%Y/%j'
    d['out_dir_parent'] =    '/home/sysop/workflow_tests/conv_tests/'
    d['out_dir_structure'] = '<site_id9>/%Y/%j'
    
    return d


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
