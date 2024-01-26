#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  7 12:07:18 2023

@author: psakicki
"""

from geodezyx import utils,operational
import autorino.convert as arocnv
from rinexmod import rinexmod_api
from pathlib import Path
import gzip
import os
import re 
import numpy as np
import datetime as dt
import dateutil
import docker
import pandas as pd
import shutil

import autorino.general as arogen



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


class ConvertRinexModGnss(arogen.StepGnss):
    def __init__(self,out_dir,tmp_dir,log_dir,
                 epoch_range,
                 site=None,
                 session=None,
                 site_id=None,
                 sitelogs=None):
    
        super().__init__(out_dir,tmp_dir,log_dir,
                         epoch_range,
                         site=site,
                         session=session,
                         site_id=site_id)

        ### temp dirs init
        self._set_conv_tmp_dirs_paths() 

        ### sitelog init
        if sitelogs:
            self.sitelogs = rinexmod_api.sitelog_input_manage(sitelogs,
                                                              force=False)
        else:
            self.sitelogs = None
            
    ########### ConvertRinexModGnss specific methods        

    def _set_conv_tmp_dirs_paths(self, 
                                 tmp_subdir_logs='logs',
                                 tmp_subdir_unzip='unzipped',
                                 tmp_subdir_conv='converted',
                                 tmp_subdir_rnxmod='rinexmoded'):

        self.tmp_dir_logs = os.path.join(self.tmp_dir,
                                         tmp_subdir_logs)
        self.tmp_dir_unzipped = os.path.join(self.tmp_dir,
                                         tmp_subdir_unzip)
        self.tmp_dir_converted = os.path.join(self.tmp_dir,
                                              tmp_subdir_conv)
        self.tmp_dir_rinexmoded = os.path.join(self.tmp_dir,
                                               tmp_subdir_rnxmod) 

        utils.create_dir(self.tmp_dir_logs)
        utils.create_dir(self.tmp_dir_unzipped)
        utils.create_dir(self.tmp_dir_converted)
        utils.create_dir(self.tmp_dir_rinexmoded)

        return self.tmp_dir_logs, self.tmp_dir_unzipped, \
            self.tmp_dir_converted, self.tmp_dir_rinexmoded 
        
    def convert_rnxmod(self):
        ###############################################
        if self.sitelogs:
            site4_list = site_list_from_sitelogs(self.sitelogs)
        else:
            site4_list = []
        
        ### initialize the table as log
        self.set_table_log(out_dir=self.tmp_dir_logs)
        # ts = utils.get_timestamp()
        # log_table = os.path.join(tmpdir_logs,ts + "_conv_table.log")
        # log_table_df_void = pd.DataFrame([], columns=self.table.columns)
        # log_table_df_void.to_csv(log_table,mode="w",index=False)

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

            ### manage compressed files
            if ext in ('.GZ','.7Z','.7ZIP','.ZIP','.Z'):
                logger.debug("%s is compressed",fraw)
                fraw = Path(gunzip(fraw, self.tmp_dir_unzipped))
 
            ### since the site code from fraw can be poorly formatted
            # we search it w.r.t. the sites from the sitelogs
            site =  _site_search_from_list(fraw,
                                           site4_list)     

            tmp_dir_rinexmoded_use = os.path.join(self.tmp_dir_rinexmoded,
                                                  site.upper())
                                                 
            utils.create_dir(tmp_dir_rinexmoded_use)
            
            ### do a first converter selection by removing odd files 
            conve = _select_conv_odd_file(fraw)
            
            logger.info("extension/converter: %s/%s",ext,conve)
        
            if not conve:
                logger.info("file skipped, no converter found: %s",fraw)
                self.table.loc[irow,'note'] = "no converter found"
                self.table.loc[irow,'ok_inp'] = False 
                self.write_in_table_log(self.table.loc[irow])
                continue
            
            ### a fonction to stop the docker conteners running for too long
            # (for trimble conversion)
            stop_long_running_containers()
            
            #############################################################
            ###### CONVERSION
            self.table.loc[irow,'ok_inp'] = True
    
            frnxtmp, _ = arocnv.converter_run(fraw,
                                              self.tmp_dir_converted,
                                              converter = conve)
            if frnxtmp:
                ### update table if things go well
                self.table.loc[irow,'fpath_out'] = frnxtmp
                epo_srt_ok, epo_end_ok = operational.rinex_start_end(frnxtmp)
                self.table.loc[irow,'epoch_srt'],\
                    self.table.loc[irow,'epoch_end'] = epo_srt_ok, epo_end_ok 
                self.table.loc[irow,'ok_out'] = True
            else:
                ### update table if things go wrong
                self.table.loc[irow,'ok_out'] = False
    
            #############################################################
            ###### RINEXMOD            
            try:
                frnxfin = rinexmod_api.rinexmod(frnxtmp,
                                                tmp_dir_rinexmoded_use,
                                                marker=site,
                                                compression="gz",
                                                longname=True,
                                                sitelog=self.sitelogs,
                                                force_rnx_load=True,
                                                verbose=False,
                                                full_history=True)
                ### update table if things go well
                self.table.loc[irow,'ok_out'] = True
                self.table.loc[irow,'fpath_out'] = frnxfin
                self.table.loc[irow,'size_out'] = os.path.getsize(frnxfin)
                                           
                self.write_in_table_log(self.table.loc[irow])
                
            except Exception as e:
                ### update table if things go wrong
                logger.error(e)
                self.table.loc[irow,'ok_out'] = False
                self.write_in_table_log(self.table.loc[irow])

                continue

            #############################################################
            ###### FINAL MOVE                             
            ### def output folders        
            #### !!!!! ADD THE EXCEPTION AND TABLE UPDATE !!!!
            outdir_use = arogen.translator(self.out_dir,
                                           self.table.loc[irow,'epoch_srt'], 
                                           self.translate_dict)
            ### do the move 
            utils.create_dir(outdir_use)
            shutil.copy(frnxfin,outdir_use)
                
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

def _select_conv_odd_file(fraw_inp,
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
    else:
    ### per default
        conve = "auto"
        for ext_exl in ext_excluded:
            if re.match(ext_exl,ext):
                conve = None    
                logger.warn("%s will be skipped, excluded extention %s",
                            fraw.name,
                            ext_exl)
                break
            
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

def gunzip(gzip_file_inp, out_dir_inp = None):
    gzip_file = Path(gzip_file_inp)

    if not out_dir_inp:
        out_dir = gzip_file.parent
    else:
        out_dir = Path(out_dir_inp)

    file_out = out_dir.joinpath(gzip_file.stem)

    with gzip.open(gzip_file_inp, 'rb') as f_in:
        with open(file_out, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    return str(file_out)




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
    
