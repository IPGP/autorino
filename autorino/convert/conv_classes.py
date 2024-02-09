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
import os
import re 
import numpy as np
import datetime as dt
import dateutil
import docker
import shutil
import autorino.general as arogen



#### Import the logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel("INFO")

class ConvertRinexModGnss(arogen.StepGnss):
    def __init__(self,out_dir,tmp_dir,log_dir,
                 epoch_range,
                 site=None,
                 session=None,
                 sitelogs=None):
    
        super().__init__(out_dir,tmp_dir,log_dir,
                         epoch_range,
                         site=site,
                         session=session)

        ### temp dirs init
        self._init_conv_tmp_dirs_paths() 

        ### sitelog init
        if sitelogs:
            sitelogs_set = self.translate_path(sitelogs)
            self.sitelogs = rinexmod_api.sitelog_input_manage(sitelogs_set,
                                                              force=False)
        else:
            self.sitelogs = None
            
    ########### ConvertRinexModGnss specific methods        

    def _init_conv_tmp_dirs_paths(self, 
                                  tmp_subdir_logs='logs',
                                  tmp_subdir_unzip='unzipped',
                                  tmp_subdir_conv='converted',
                                  tmp_subdir_rnxmod='rinexmoded'):
        
        """
        initialize temp dirs, but keeps their generic form, with <...> and %X,
        and without creating them 
        
        sees set_conv_tmp_dirs_paths() for the effective translation and 
        creation of these temp dirs
        """
 
        ### internal (_) versions have not been translated
        self._tmp_dir_logs = os.path.join(self.tmp_dir,
                                         tmp_subdir_logs)
        self._tmp_dir_unzipped = os.path.join(self.tmp_dir,
                                         tmp_subdir_unzip)
        self._tmp_dir_converted = os.path.join(self.tmp_dir,
                                              tmp_subdir_conv)
        self._tmp_dir_rinexmoded = os.path.join(self.tmp_dir,
                                               tmp_subdir_rnxmod) 
        
        ### translation
        self.tmp_dir_logs = self.translate_path(self._tmp_dir_logs)
        self.tmp_dir_unzipped = self.translate_path(self.tmp_dir_unzipped)
        self.tmp_dir_converted = self.translate_path(self.tmp_dir_converted)
        self.tmp_dir_rinexmoded = self.translate_path(self.tmp_dir_rinexmoded)

        return self.tmp_dir_logs, self.tmp_dir_unzipped, \
            self.tmp_dir_converted, self.tmp_dir_rinexmoded 
            
            
    def set_conv_tmp_dirs_paths(self):
        """
        effective translation and creation of temp dirs
        """
        
        #### this translation is now  useless, is also done in _init_conv_tmp_dirs_paths
        tmp_dir_logs_set = self.translate_path(self.tmp_dir_logs)
        tmp_dir_unzipped_set = self.translate_path(self.tmp_dir_unzipped)
        tmp_dir_converted_set = self.translate_path(self.tmp_dir_converted)
        tmp_dir_rinexmoded_set = self.translate_path(self.tmp_dir_rinexmoded)
        
        utils.create_dir(tmp_dir_logs_set)
        utils.create_dir(tmp_dir_unzipped_set)
        utils.create_dir(tmp_dir_converted_set)
        utils.create_dir(tmp_dir_rinexmoded_set)
        
        return tmp_dir_logs_set, tmp_dir_unzipped_set, tmp_dir_converted_set, tmp_dir_rinexmoded_set
    
    ###############################################

    def convert_rnxmod(self,print_table=False):
        if self.sitelogs:
            site4_list = site_list_from_sitelogs(self.sitelogs)
        else:
            site4_list = []
        
        tmp_dir_logs_use,_,_,_ = self.set_conv_tmp_dirs_paths()

        ### initialize the table as log
        self.set_table_log(out_dir=tmp_dir_logs_use)

        ### get a table with only the good files (ok_inp == True)
        table_init_ok = self.filter_purge()
        n_ok_inp = (self.table['ok_inp']).sum()
        n_not_ok_inp = np.logical_not(self.table['ok_inp']).sum()
        
        logger.info("******** RINEX conversion / Header mod ('rinexmod') for %6i files",
                    n_ok_inp)        
        
        logger.info("%6i files are excluded",
                    n_not_ok_inp)
        
        if print_table:
            self.print_table()
            
        ######################### START THE LOOP ##############################
        for irow,row in table_init_ok.iterrows(): 
            fraw = Path(row['fpath_inp'])
            ext = fraw.suffix.lower()
            logger.info("***** input raw file for conversion: %s",
                        fraw.name)

            _, tmp_dir_unzipped_use, tmp_dir_converted_use, tmp_dir_rinexmoded_use = self.set_conv_tmp_dirs_paths()

            ### manage compressed files
            # not here anymore
            #if ext in ('.gz',):
            #    logger.debug("%s is compressed",fraw)
            #    fraw = Path(arogen.decompress(fraw, tmp_dir_unzipped_use))
 
            ### since the site code from fraw can be poorly formatted
            # we search it w.r.t. the sites from the sitelogs
            site =  _site_search_from_list(fraw,
                                           site4_list)     

            
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
                                              tmp_dir_converted_use, 
                                              converter = conve)
            if frnxtmp:
                ### update table if things go well
                self.table.loc[irow,'fpath_out'] = frnxtmp
                epo_srt_ok, epo_end_ok = operational.rinex_start_end(frnxtmp)
                self.table.loc[irow,'epoch_srt'] = epo_srt_ok
                self.table.loc[irow,'epoch_end'] = epo_end_ok 
                self.table.loc[irow,'ok_out'] = True
            else:
                ### update table if things go wrong
                self.table.loc[irow,'ok_out'] = False
    
            #############################################################
            ###### RINEXMOD            
            try:
                frnxmod = rinexmod_api.rinexmod(frnxtmp,
                                                tmp_dir_rinexmoded_use,
                                                marker=site,
                                                compression="gz",
                                                longname=True,
                                                sitelog=self.sitelogs,
                                                force_rnx_load=True,
                                                verbose=False,
                                                tolerant_file_period=True,
                                                full_history=True)
                ### update table if things go well
                self.table.loc[irow,'ok_out'] = True
                self.table.loc[irow,'fpath_out'] = frnxmod
                self.table.loc[irow,'size_out'] = os.path.getsize(frnxmod)
                                           
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
            outdir_use = self.translate_path(self.out_dir,
                                             epoch_inp=self.table.loc[irow,
                                                                      'epoch_srt'])
            try:
                ### do the move 
                utils.create_dir(outdir_use)
                frnxfin = shutil.copy2(frnxmod,outdir_use)
                self.table.loc[irow,'ok_out'] = True
                self.table.loc[irow,'fpath_out'] = frnxfin
                self.table.loc[irow,'size_out'] = os.path.getsize(frnxfin)
            except Exception as e:
                logger.error(e)
                self.table.loc[irow,'ok_out'] = False
                self.write_in_table_log(self.table.loc[irow])
                continue               
                
        return None


#########################################################################
#### Misc functions 

def site_list_from_sitelogs(sitelogs_inp):
    """
    From a list of sitelogs, get a site id list (4 chars)
    """
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


#################################################
############ FUNCTION GRAVEYARD
