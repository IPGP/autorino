#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  7 12:07:18 2023

@author: psakicki
"""

from geodezyx import utils,  operational
import autorino.convert as arocnv
import rinexmod_api
from pathlib import Path
import os
import re 
import numpy as np
import datetime as dt
import dateutil
import docker
import pandas as pd
import shutil

from autorino import general as arogen

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


class ConvertRinexModGnss(arogen.WorkflowGnss):
    def __init__(self,session,epoch_range,out_dir,tmp_dir,sitelogs=None):
        self.session = session
        self.epoch_range = epoch_range ### setter bellow
        self.out_dir = out_dir
        self.tmp_dir = tmp_dir
        self.table = self._table_init()
        
        if sitelogs:
            self.sitelogs = rinexmod_api.sitelog_input_manage(sitelogs,
                                                              force=False)   

    ######## internal methods 
    # def _table_init(self,table_cols=):
        # # df = pd.DataFrame(columns=["epoch","fname",
        # #                            "ok_remote",
        # #                            "ok_local",
        # #                            "fpath_remote",
        # #                            "fpath_local",
        # #                            "size_local"])
                                   
        # # df.epoch = self.epoch_range.epoch_range_list()
        # # df.set_index("epoch",inplace=True,drop=True)
        # # df = df.where(pd.notnull(df), None)        
        
        # table_cols = ['fraw',
                      # 'site',
                      # 'epoch',
                      # 'ok_inp',
                      # 'ok_conv',
                      # 'ok_rnxmod',
                      # 'frnx_tmp',
                      # 'frnx_fin',
                      # 'note']
        
        # df = pd.DataFrame([], columns=table_cols)
        
        # return df
    
    
    def load_table_from_filelist(self,
                                 input_files,
                                 inp_regex=".*"):
        
        
        flist = input_list_reader(input_files,
                                  inp_regex)
                
        self.table['fraw'] = flist
        self.table['ok_inp'] = self.table['fraw'].apply(os.path.isfile)
        
        return flist
        
    def load_table_from_download_table(self,
                                       input_table):
                                           
        self.table['fpath_inp'] = input_table['fpath_out'].values
        self.table['fname'] = self.table['fpath_inp'].apply(os.path.basename)
        self.table['site'] = input_table['site'].values
        self.table['epoch'] = input_table['epoch'].values
        self.table['ok_inp'] = self.table['fpath_inp'].apply(os.path.isfile)
        
        return None

        
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
        nfil = 0 
        
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
        
        #############################'
    
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
    
    def conv_rnxmod_files(self):
        
        ###############################################
        ### def temp folders
        tmpdir_logs = self.session.tmp_dir + "/logs"
        tmpdir_converted = self.session.tmp_dir + "/converted"
        tmpdir_rinexmoded = self.session.tmp_dir + "/rinexmoded" 
        
        utils.create_dir(tmpdir_logs)
        utils.create_dir(tmpdir_converted)
                
        site4_list = site_list_from_sitelogs(self.sitelogs)
        
        ### initialize the table as log
        ts = utils.get_timestamp()
        log_table = os.path.join(tmpdir_logs,ts + "_conv_table.log")
        log_table_df_void = pd.DataFrame([], columns=self.table.columns)
        log_table_df_void.to_csv(log_table,mode="w",index=False)
        
        ### get a table with only the good files (ok_inp == True)
        table_init_ok = self.filter_purge()
        n_ok_inp = (self.table['ok_inp']).sum()
        n_not_ok_inp = np.logical_not(self.table['ok_inp']).sum()
        
        logger.info("******** RINEX conversion / Header mod ('rinexmod') for %6i files",
                    n_ok_inp)        
        
        logger.info("%6i files are excluded",
                    n_not_ok_inp)
        
        for irow,row in table_init_ok.iterrows(): 
             
            fraw = Path(row['fpath_inp'])
            ext = fraw.suffix.upper()
            logger.info("***** input raw file for conversion: %s",
                        fraw.name)
    
            ### since the site code from fraw can be poorly formatted
            # we search it w.r.t. the sites from the sitelogs
            site =  _site_search_from_list(fraw,
                                           site4_list)     

            tmpdir_rinexmoded_use = os.path.join(tmpdir_rinexmoded,
                                                 site.upper())
                                                 
            utils.create_dir(tmpdir_rinexmoded_use)
            
            ### find the right converter
            conve = select_converter_batch(fraw)
            
            logger.info("extension/converter: %s/%s",ext,conve)
        
            if not conve:
                logger.info("file skipped, no converter found: %s",fraw)
                row.note = "no converter found"
                row.ok_inp = False
                row.to_csv(log_table, mode="a", index=False, header=False)
                continue
            
            ### a fonction to stop the docker conteners running for too long
            # (for trimble conversion)
            stop_long_running_containers()
            
            #############################################################
            #### CONVERSION
            self.table.loc[irow,'ok_inp'] = True
    
            frnxtmp, _ = arocnv.converter_run(fraw,
                                            tmpdir_converted,
                                            converter = conve)
            if frnxtmp:
                self.table.loc[irow,'fpath_out'] = frnxtmp
                self.table.loc[irow,'ok_out'] = True
                self.table.loc[irow,'epoch'] , _ = operational.rinex_start_end(frnxtmp)
            else:
                self.table.loc[irow,'ok_out'] = False
    
            #############################################################
            #### RINEXMOD            
            try:
                frinfin = rinexmod_api.rinexmod(frnxtmp,
                                                tmpdir_rinexmoded_use,
                                                marker=site,
                                                compression="gz",
                                                longname=True,
                                                sitelog=self.sitelogs,
                                                force_rnx_load=True,
                                                verbose=False,
                                                full_history=True)
                self.table.loc[irow,'ok_out'] = True
                self.table.loc[irow,'fpath_out'] = frinfin
                self.table.loc[irow,'size_out'] = os.path.getsize(frinfin)
                
                pd.DataFrame(row).T.to_csv(log_table,mode="a",
                                           index=False,header=False) 
                                           
                ### def output folders        
                outdir_use = arogen.translator(self.out_dir,
                                               row.epoch,
                                               self.session.translate_dict)
                utils.create_dir(outdir_use)
                shutil.copy(frinfin,outdir_use)
                
            except Exception as e:
                logger.warn(e)
                self.table.loc[irow,'ok_out'] = False
                pd.DataFrame(row).T.to_csv(log_table,mode="a",
                                           index=False,header=False) 
                continue
        
        return None


#########################################################################
#### Misc functions 
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
                                         "Trimble",
                                         ".ORIG"]):
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
    try:
        client = docker.from_env()
    except docker.errors.DockerException:
        logger.warn('Permission denied for Docker')
        return None
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
        
    #     modify the boolean "ok_inp" of the object's table
    #     returns the filtered raw files in a list
    #     """
    #     flist_out = []
    #     nfil = 0 
        
    #     ok_inp_bool_stk = []
        
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
    #             ok_inp_bool_stk.append(False)

    #         else:
    #             if not row.ok_inp: ### ok_inp is already false
    #                 ok_inp_bool_stk.append(False)
    #             else:
    #                 ok_inp_bool_stk.append(True)
    #                 flist_out.append(f)

    #     ### final replace of ok init
    #     self.table.ok_inp = ok_inp_bool_stk

    #     logger.info("%6i files filtered, not in the year min/max range (%4i/%4i)",
    #                 nfil,year_min,year_max)
    #     return flist_out 
    
