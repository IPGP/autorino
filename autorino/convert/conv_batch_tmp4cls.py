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

def converter_batch(input_files,
                    outdir,
                    inp_regex=".*",
                    sitelogs_inp=None,
                    year_in_inp_path=None,
                    year_min_max=(1980,2099),
                    files_idx_minmax=(None,None),
                    keywords_path_excl=['Problem','Rinex','ZIP'],
                    raw_excl_list=None):
    
    
    ###############################################
    ### read input lists or regex
    flist = _input_files_reader(input_files,inp_regex)
    

    ###############################################
    ### read sitelogs        
    if os.path.isdir(sitelogs_inp):
        sitelogs = rinexmod_api.sitelog_input_manage(sitelogs_inp,
                                                     force=False)
    
    ### get the site (4chars) as a list 
    site4_list = [s.site4char for s in sitelogs]

    ###############################################
    ### def output folders
    outdir_logs = outdir + "/logs"
    outdir_converted =  outdir + "/converted"
    outdir_rinexmoded =  outdir + "/rinexmoded" 

    utils.create_dir(outdir_logs)
    
    ##############################################
    ### def output logs
    ts = utils.get_timestamp()
    ### the legacy OK/fail listare disabled, everything is in the table files
    log_table     = os.path.join(outdir_logs,ts + "_table.log")
    table_cols = ["site","date",
                  "ok_init","ok_conv","ok_rnxmod",
                  "fraw", "frnx_tmp", "frnx_fin",
                  "note"]
    
    logline = pd.DataFrame([], columns=table_cols)
    logline.to_csv(log_table,mode="w",index=False)

    ##############################################
    ### find and read previous OK list files
    prev_raw_ok_logs = utils.find_recursive(outdir_logs,'*_raw_ok.log')    
    prev_raw_ok = _input_files_reader(tuple(prev_raw_ok_logs))

    ##############################################
    ### find and read manual exclu list files
    prev_raw_exclu = _input_files_reader(raw_excl_list)

    ##############################################
    ### find and read previous table log files
    prev_table_logs = utils.find_recursive(outdir_logs,'*table.log')    
    DF_prev_tbl = pd.concat([pd.read_csv(f) for f in prev_table_logs])
    DF_prev_tbl.reset_index(inplace=True,drop=True)
    
    ##############################################
    ### filtering the input list
    flist = _filter_year_min_max(flist, year_in_inp_path, year_min_max)
    flist = _filter_prev_table(flist, DF_prev_tbl)
    flist = _filter_prev_raw_ok_or_exclu(flist, prev_raw_ok,False) ### must be disabled at one point
    flist = _filter_prev_raw_ok_or_exclu(flist, prev_raw_exclu,True)
    flist = _filter_bad_keywords(flist, keywords_path_excl)
    
    logger.info("%6i files will be processed", len(flist))

    for fraw in flist:  

        fraw = Path(fraw)
        ext = fraw.suffix.upper()
        logger.info("***** input raw file for conversion: %s",fraw.name)

        ### since the fraw name can be poorly formatted
        # we search it w.r.t. the sites from the sitelogs

        site =  _site_search_from_list(fraw,site4_list)       


        logline = pd.DataFrame([[site,None,None,None,None,
                                 fraw,"","","no comment"]],
                                 columns=table_cols)

        outdir_rinexmoded_use = os.path.join(outdir_rinexmoded,site.upper())
        utils.create_dir(outdir_converted)
        utils.create_dir(outdir_rinexmoded_use)
        
        ### find the right converter
        conve = _converter_select_batch(fraw)
        
        logger.info("extension/converter: %s/%s",ext,conve)
    
        if not conve:
            logger.info("file skipped, no converter found: %s",fraw)
            #utils.write_in_file(str(fraw), log_raw_fail, append=True)
            logline.note = "no converter found"
            logline.ok_init = False
            logline.to_csv(log_table,mode="a",index=False,header=False)
            continue
        
        ### a fonction to stop the docker conteners running for too long
        # (for trimble conversion)
        stop_long_running_containers()
        
        #############################################################
        #### CONVERSION
        logline.ok_init = True

        frnxtmp, _ = arcv.converter_run(fraw,
                                        outdir_converted,
                                        converter = conve)
        if frnxtmp:
            logline.frnx_tmp = frnxtmp
            logline.ok_conv = True
            logline.date, _ = operational.rinex_start_end(frnxtmp)
        else:
            logline.ok_conv = False

    return None

def _filter_prev_raw_ok_or_exclu(flist,prev_raw_ok,
                                 message_manu_exclu=False):
    """
    Filter a list of raw files if they are present in OK log or 
    manual exclusion list
    """
    flist_out = []
    nfil = 0 
    for f in flist:
        if f in prev_raw_ok:
            nfil += 1   
            if not message_manu_exclu:
                logger.debug("file OK during a previous run (legacy simple OK list): %s",f)
            else:
                logger.debug("file manually excluded in the exclusion list: %s",f)
        else:
            flist_out.append(f)
            
    if not message_manu_exclu:
        logger.info("%6i files OK during a previous run (legacy simple OK list)", nfil)
    else:
        logger.info("%6i files manually excluded in the exclusion list,", nfil)

    return flist_out


def _filter_bad_keywords(flist,keywords_path_excl):
    """
    Filter a list of raw files if the full path contains certain keywords
    """
    flist_out = []
    nfil = 0 
    for f in flist:
        boolbad = utils.patterns_in_string_checker(f,*keywords_path_excl)
        if boolbad:
            logger.debug("file excluded, contains an excluded keyword: %s",f)
            nfil += 1
        else:
            flist_out.append(f)
    logger.info("%6i files excluded, their paths contain bad keywords", nfil)
    return flist_out
            
            
def _filter_year_min_max(flist,year_in_inp_path,year_min_max):
    """
    Filter a list of raw files if they are not in a year range
    it is the year in the file path which is tested
    year_in_inp_path is the postiion of the year in the absolute path
    
    
    year min and year max are included in the range
    """
    flist_out = []
    nfil = 0 
    for f in flist:
        try:
            year_folder = int(f.split("/")[year_in_inp_path])
        except:
            logger.warning("unable to convert the given value of the year as int")
            continue
        if year_folder < year_min_max[0] or year_folder > year_min_max[1]:
            logger.debug("file excluded, not in year range (%s): %s",
                         year_folder,f)
            nfil += 1
        else:
            flist_out.append(f)
    logger.info("%6i files excluded, not in the year min/max range (%4i/%4i)", nfil,year_min_max[0],year_min_max[1])
    return flist_out 


def _filter_prev_table(flist,
                       DF_prev_tab):
        
    DFflist_orig = pd.Series(flist)
    DFflist_rerun = DFflist_orig.copy()
    
    col_ok_names = ["ok_init","ok_conv","ok_rnxmod"]
    
    #### lines when everthing is ok
    DFbool_OK = DF_prev_tab[col_ok_names].apply(np.logical_and.reduce,axis=1)
    DFfiles_OK = DF_prev_tab[DFbool_OK]
    DFfiles_bad = DF_prev_tab[~ DFbool_OK]
    # NB: substraction of the OK files from the DFflist_use is done in a final step
    
    logger.info("%6i files OK during a previous run (table list)", len(DFfiles_OK))
    
    ###### Final substraction 
    ### of the OK files
    if len(DFfiles_OK) > 0:
        DFflist_rerun = DFflist_rerun[ ~ (DFflist_rerun.isin(DFfiles_OK.fraw))]

    return list(DFflist_rerun)

def _site_search_from_list(fraw_inp,site4_list_inp):
    """
    from a raw file with an approximate site name and a list of correct site names, search the correct site name of the raw file
    """
    site_out = None
    for s4 in site4_list_inp:
        if re.search(s4,fraw_inp.name,re.IGNORECASE):
            site_out = s4
            break
    if not site_out: # last chance, get the 4 1st chars of the raw file
        site_out = fraw_inp.name[:4]
    return site_out

def _converter_select_batch(fraw_inp):

    fraw = Path(fraw_inp)
    ext = fraw.suffix.upper()

    if not ext or len(ext) == 0:
        conve = "tps2rin"
    elif re.match(".M[0-9][0-9]", ext):
        conve = "mdb2rinex"
    ### here we skip all the weird files
    elif re.match(".TG!$",ext) or re.match(".DAT",ext) or re.match(".Z",ext) or re.match(".BCK",ext) or re.match("^.[0-9]{3}$",ext) or re.match(".A$",ext) or re.match("Trimble",ext):
        conve = None
    else:
        conve = "auto"
        
    return conve

def _input_files_reader(inp_fil,inp_regex=".*"):
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


def _filter_prev_table_advanced(flist,
                        DF_prev_tab,
                        rerun_ok_step=(True,False,False)):
        
    DFflist_orig = pd.Series(flist)
    DFflist_rerun = DFflist_orig.copy()
    
    col_ok_names = ["ok_init","ok_conv","ok_rnxmod"]
    
    #### lines when everthing is ok
    DFbool_OK = DF_prev_tab[col_ok_names].apply(np.logical_and.reduce,axis=1)
    DFfiles_OK = DF_prev_tab[DFbool_OK]
    DFfiles_bad = DF_prev_tab[~ DFbool_OK]
    
    # NB: substraction of the OK files from the DFflist_use is done in a final step
    
    # logger.info("%s files OK during a previous run", DFfiles_OK.sum())
    
    if len(DFfiles_bad) > 0:
        rerun_lba = lambda x: [np.logical_or(x[i],rerun_ok_step[i]) for i in range(len(col_ok_names))]
        DFrerun_bool = DFfiles_bad[col_ok_names].apply(rerun_lba,axis=1)
        DFrerun_bool = DFrerun_bool.apply(np.logical_or.reduce,axis=0)
        DFfiles_skip = DFfiles_bad[~ DFrerun_bool]
    
    ###### Final substraction 
    ### of the OK files
    DFflist_rerun = DFflist_rerun[ ~ (DFflist_rerun.isin(DFfiles_OK.fraw))]
    ### of the bad files definitely skipped
    if len(DFfiles_bad) > 0:
        DFflist_rerun = DFflist_rerun[ ~ (DFflist_rerun.isin(DFfiles_skip.fraw))]
    
    return list(DFflist_rerun)
