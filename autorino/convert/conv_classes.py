#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  7 12:07:18 2023

@author: psakicki
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  8 18:45:58 2023

@author: psakicki
"""

from geodezyx import utils,  operational
import autorino.convert as arcv
import rinexmod_api
from pathlib import Path
import os
import re 
import numpy as np
import datetime as dt
import dateutil
import docker
import pandas as pd

#### Import the logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel("INFO")


def site_list_from_sitelogs(sitelogs_inp):
    ###############################################
    ### read sitelogs        
    if not type(sitelogs_inp) is list and os.path.isdir(sitelogs_inp):
        sitelogs = rinexmod_api.sitelog_input_manage(sitelogs_inp,
                                                     force=False)
    else:
        sitelogs = sitelogs_inp
    
    ### get the site (4chars) as a list 
    site4_list = [s.site4char for s in sitelogs]
    
    return site4_list



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


class ConvertRinexModGnss():
    def __init__(self,session,epoch_range,out_dir,tmp_dir,sitelogs):
        self.session = session
        self.epoch_range = epoch_range ### setter bellow
        self.out_dir = out_dir
        self.tmp_dir = tmp_dir
        self.table = self._table_init()
        
        self.sitelogs = rinexmod_api.sitelog_input_manage(sitelogs,
                                                          force=False)   
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
        # df = pd.DataFrame(columns=["epoch","fname",
        #                            "ok_remote",
        #                            "ok_local",
        #                            "fpath_remote",
        #                            "fpath_local",
        #                            "size_local"])
                                   
        # df.epoch = self.epoch_range.epoch_range_list()
        # df.set_index("epoch",inplace=True,drop=True)
        # df = df.where(pd.notnull(df), None)        
        
        table_cols = ["fraw","site","epoch",
                      "ok_init","ok_conv","ok_rnxmod",
                      "frnx_tmp", "frnx_fin",
                      "note"]
        
        df = pd.DataFrame([], columns=table_cols)
        
        return df
    
    
    def load_table_from_filelist(self,
                                 input_files,
                                 inp_regex=".*"):
        
        
        flist = input_list_reader(input_files,
                                  inp_regex)
                
        self.table.fraw = flist
        self.table.ok_init = self.table.fraw.apply(os.path.isfile)
        
        return flist
        
    def filter_bad_keywords(self,keywords_path_excl):
        """
        Filter a list of raw files if the full path contains certain keywords
        
        modify the boolean "ok_init" of the object's table
        returns the filtered raw files in a list
        """
        flist_out = []
        ok_init_bool_stk = []
        nfil = 0 
        for irow,row in self.table.iterrows():
            f = row.fraw
            boolbad = utils.patterns_in_string_checker(f,*keywords_path_excl)
            if boolbad:
                self.table.iloc[irow,'ok_init'] = False
                logger.debug("file filtered, contains an excluded keyword: %s",
                             f)
                nfil += 1
            else:
                if not row.ok_init: ### ok_init is already false
                    ok_init_bool_stk.append(False)
                else:
                    ok_init_bool_stk.append(True)
                    flist_out.append(f)
                    
        ### final replace of ok init
        self.table.ok_init = ok_init_bool_stk
                    
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
        
        modify the boolean "ok_init" of the object's table
        returns the filtered raw files in a list
        """
        flist_out = []
        nfil = 0 
        
        ok_init_bool_stk = []
        
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
            
        years = self.table.fraw.apply(_year_detect,args=(year_in_inp_path,))
        
        bool_out_range = (years < year_min) | (years > year_max)
        bool_in_range = np.logical_not(bool_out_range)
        
        #############################'
    
        ok_init_bool_stk = bool_in_range & self.table.ok_init 
        nfil_total = sum(bool_out_range)
        ### logical inhibition a.\overline{b}
        nfil_spec = sum(np.logical_and(bool_out_range, self.table.ok_init))
        
        ### final replace of ok init
        self.table.ok_init = ok_init_bool_stk

        logger.info("%6i/%6i files filtered (total/specific) not in the year min/max range (%4i/%4i)",
                    nfil_total, nfil_spec ,year_min,year_max)

        return flist_out 
    

    
    def filter_filelist(self,filelist_exclu_inp,
                              message_manu_exclu=False):
        """
        Filter a list of raw files if they are present in a text file list 
        e.g. an OK log or manual exclusion list
        
        modify the boolean "ok_init" of the object's table
        returns the filtered raw files in a list
        """
        
        flist_exclu = input_list_reader(filelist_exclu_inp)
        
        flist_out = []
        ok_init_bool_stk = []
        
        nfil = 0 
        for irow,row in self.table.iterrows():
            f = row.fraw
            if f in flist_exclu:
                nfil += 1
                ok_init_bool_stk.append(False)
                if not message_manu_exclu:
                    logger.debug("file filtered, was OK during a previous run (legacy simple list): %s",f)
                else:
                    logger.debug("file filtered manually in the exclusion list: %s",f)
            else:
                if not row.ok_init: ### ok_init is already false
                    ok_init_bool_stk.append(False)
                else:
                    ok_init_bool_stk.append(True)
                    flist_out.append(f)
            
        if not message_manu_exclu:
            logger.info("%6i files filtered, were OK during a previous run (legacy simple OK list)", nfil)
        else:
            logger.info("%6i files manually filtered in the exclusion list,", nfil)
            
        ### final replace of ok init
        self.table.ok_init = ok_init_bool_stk
    
        return flist_out    
    
    def filter_previous_tables(self,
                               DF_prev_tab):
        """
        Filter a list of raw files if they are present in previous 
        conversion tables stored as log
        
        modify the boolean "ok_init" of the object's table
        returns the filtered raw files in a list
        """
        
        col_ok_names = ["ok_init","ok_conv","ok_rnxmod"]
        
        #### previous files when everthing was ok
        prev_bool_ok = DF_prev_tab[col_ok_names].apply(np.logical_and.reduce,
                                                       axis=1)
                
        prev_files_ok = DF_prev_tab[prev_bool_ok].fraw
        
        ### current files which have been already OK and which have already 
        ### ok_init == False
        ### here the boolean value are inverted compared to the table:
        # True = skip me / False = keep me 
        # a logical not inverts everything at the end
        curr_files_ok_prev = self.table.fraw.isin(prev_files_ok)
        curr_files_off_already = np.logical_not(self.table.ok_init)
        
        curr_files_skip = np.logical_or(curr_files_ok_prev,
                                        curr_files_off_already)

        self.table.ok_init = np.logical_not(curr_files_skip)
        
        logger.info("%6i files filtered, were OK during a previous run (table list)",
                    curr_files_ok_prev.sum())
        
        flist_out = list(self.table.fraw[self.table.ok_init])

        return flist_out
    
    def filter_purge(self,inplace=False):
        if inplace:
            self.table = self.table[self.table.ok_init]
            out = list(self.table.fraw)
        else:
            out = self.table[self.table.ok_init]
        return out
    
    def conv_rnxmod_files(self):
        
        ###############################################
        ### def output folders
        outdir_logs = self.out_dir + "/logs"
        outdir_converted =  self.out_dir + "/converted"
        outdir_rinexmoded =  self.out_dir + "/rinexmoded" 

        utils.create_dir(outdir_logs)
        utils.create_dir(outdir_converted)
        
        site4_list = site_list_from_sitelogs(self.sitelogs)
        
        ### initialize the table as log
        ts = utils.get_timestamp()
        log_table = os.path.join(outdir_logs,ts + "_conv_table.log")
        log_table_df_void = pd.DataFrame([], columns=self.table.columns)
        log_table_df_void.to_csv(log_table,mode="w",index=False)
        
        ### get a table with only the good files (ok_init == True)
        table_init_ok = self.filter_purge()
        n_ok_init = (self.table.ok_init).sum()
        n_not_ok_init = np.logical_not(self.table.ok_init).sum()
        
        logger.info("******** RINEX conversion / Header mod ('rinexmod') for %6i files",
                    n_ok_init)        
        
        logger.info("%6i files are excluded",
                    n_not_ok_init)
        
        for irow,row in table_init_ok.iterrows():  
            
            fraw = Path(row.fraw)
            ext = fraw.suffix.upper()
            logger.info("***** input raw file for conversion: %s",fraw.name)
    
            ### since the site code from fraw can be poorly formatted
            # we search it w.r.t. the sites from the sitelogs
            site =  _site_search_from_list(fraw,
                                           site4_list)       

            outdir_rinexmoded_use = os.path.join(outdir_rinexmoded,
                                                 site.upper())
            utils.create_dir(outdir_rinexmoded_use)

            ### find the right converter
            conve = select_converter_batch(fraw)
            
            logger.info("extension/converter: %s/%s",ext,conve)
        
            if not conve:
                logger.info("file skipped, no converter found: %s",fraw)
                row.note = "no converter found"
                row.ok_init = False
                row.to_csv(log_table, mode="a", index=False, header=False)
                continue
            
            ### a fonction to stop the docker conteners running for too long
            # (for trimble conversion)
            stop_long_running_containers()
            
            #############################################################
            #### CONVERSION
            row.ok_init = True
    
            frnxtmp, _ = arcv.converter_run(fraw,
                                            outdir_converted,
                                            converter = conve)
            if frnxtmp:
                row.frnx_tmp = frnxtmp
                row.ok_conv = True
                row.date, _ = operational.rinex_start_end(frnxtmp)
            else:
                row.ok_conv = False
    
    
            #############################################################
            #### RINEXMOD            
            try:
                frinfin = rinexmod_api.rinexmod(frnxtmp,
                                                outdir_rinexmoded_use,
                                                marker=site,
                                                compression="gz",
                                                longname=True,
                                                sitelog=self.sitelogs,
                                                force_rnx_load=True,
                                                verbose=False,
                                                full_history=True)
                row.ok_rnxmod = True
                row.frnx_fin = frinfin
                
                pd.DataFrame(row).T.to_csv(log_table,mode="a",
                                           index=False,header=False) 
            except:
                row.ok_rnxmod = False
                pd.DataFrame(row).T.to_csv(log_table,mode="a",
                                           index=False,header=False) 
                continue
    
        return None
    

# def converter_batch(input_files,
#                     outdir,
#                     inp_regex=".*",
#                     sitelogs_inp=None,
#                     year_in_inp_path=None,
#                     year_min_max=(1980,2099),
#                     files_idx_minmax=(None,None),
#                     keywords_path_excl=['Problem','Rinex','ZIP'],
#                     raw_excl_list=None):
    
    # ##############################################
    # ### def output logs
    # ts = utils.get_timestamp()
    # log_table = os.path.join(outdir_logs,ts + "_table.log")

    # logline.to_csv(log_table,mode="w",index=False)

    # ##############################################
    # ### find and read previous OK list files
    # prev_raw_ok_logs = utils.find_recursive(outdir_logs,'*_raw_ok.log')    
    # prev_raw_ok = _input_files_reader(tuple(prev_raw_ok_logs))

    # ##############################################
    # ### find and read manual exclu list files
    # prev_raw_exclu = _input_files_reader(raw_excl_list)

    # ##############################################

    # ##############################################
    # ### filtering the input list
    # flist = _filter_prev_table(flist, DF_prev_tbl)
    # flist = _filter_prev_raw_ok_or_exclu(flist, prev_raw_ok,False) ### must be disabled at one point
    # flist = _filter_prev_raw_ok_or_exclu(flist, prev_raw_exclu,True)
    
    # logger.info("%6i files will be processed", len(flist))


def _site_search_from_list(fraw_inp,site4_list_inp):
    """
    from a raw file with an approximate site name and a list of correct 
    site names, search the correct site name of the raw file
    """
    site_out = None
    for s4 in site4_list_inp:
        if re.search(s4,fraw_inp.name,re.IGNORECASE):
            site_out = s4
            break
    if not site_out: # last chance, get the 4 1st chars of the raw file
        site_out = fraw_inp.name[:4]
    return site_out

def select_converter_batch(fraw_inp,
                           ext_excluded=[".TG!$",
                                         ".DAT",
                                         ".Z",
                                         ".BCK",
                                         "^.[0-9]{3}$",
                                         ".A$",
                                         "Trimble"]):
    """
    do a high level case matching to identify the right converter 
    for raw file with an unconventional extension, or exclude the file
    if its extension matches an excluded one
    """    
    
    fraw = Path(fraw_inp)
    ext = fraw.suffix.upper()

    if not ext or len(ext) == 0:
        conve = "tps2rin"
    elif re.match(".M[0-9][0-9]", ext):
        conve = "mdb2rinex"
    ### here we skip all the weird files    
    elif np.any([bool(re.match(exclu,ext)) for exclu in ext_excluded]):
        conve = None
    else:
        ### per default
        conve = "auto"
        
    return conve

def stop_long_running_containers(max_running_time=120):
    """
    kill Docker container running for a too long time
    Useful for the trm2rinex dockers
    """
    client = docker.from_env()
    containers = client.containers.list()

    for container in containers:
        ### Calculate the time elapsed since the container was started
        #created_at = container.attrs['Created']
        started_at = container.attrs['State']['StartedAt']
        
        started_at =  dateutil.parser.parse(started_at)
        elapsed_time = dt.datetime.now(dt.timezone.utc) - started_at
        
        if elapsed_time > dt.timedelta(seconds=max_running_time):
            container.stop()
            logger.warning(f'Stopped container {container.name} after {elapsed_time} seconds.')
            
    return None


#################################################
############ FUNCTION GRAVEYARD


    # def filter_year_min_max_non_pythonic(self,
    #                                      year_min=1980,
    #                                      year_max=2099,
    #                                      year_in_inp_path=None):
    #     """
    #     Filter a list of raw files if they are not in a year range
    #     it is the year in the file path which is tested
        
    #     year_in_inp_path is the position of the year in the absolute path
    #     e.g.
    #     if the absolute path is:
    #     /home/user/input_data/raw/2011/176/PSA1201106250000a.T00
    #     year_in_inp_path is 4
        
    #     if no year_in_inp_path provided, a regex search is performed
    #     (more versatile, but less robust)
        
        
    #     year min and year max are included in the range
        
    #     modify the boolean "ok_init" of the object's table
    #     returns the filtered raw files in a list
    #     """
    #     flist_out = []
    #     nfil = 0 
        
    #     ok_init_bool_stk = []
        
    #     for irow,row in self.table.iterrows():
    #         f = row.fraw
    #         try:
    #             if year_in_inp_path:
    #                 year_folder = int(f.split("/")[year_in_inp_path])
    #             else:
    #                 rgx = re.search("\/(19|20)[0-9]{2}\/",f)
    #                 year_folder = int(rgx.group()[1:-1])       
    #         except:
    #             logger.warning("unable to get the year in path: %s",f)
    #             continue
            
    #         if year_folder < year_min or year_folder > year_max:
    #             logger.debug("file filtered, not in year range (%s): %s",
    #                          year_folder,f)
    #             nfil += 1
    #             ok_init_bool_stk.append(False)

    #         else:
    #             if not row.ok_init: ### ok_init is already false
    #                 ok_init_bool_stk.append(False)
    #             else:
    #                 ok_init_bool_stk.append(True)
    #                 flist_out.append(f)

    #     ### final replace of ok init
    #     self.table.ok_init = ok_init_bool_stk

    #     logger.info("%6i files filtered, not in the year min/max range (%4i/%4i)",
    #                 nfil,year_min,year_max)
    #     return flist_out 
    