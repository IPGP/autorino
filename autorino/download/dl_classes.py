#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ftplib
import pandas as pd
import os
import shutil
import autorino.download as arodl
import autorino.general as arogen

pd.options.mode.chained_assignment = 'warn'

# Create a logger object.
import logging
logger = logging.getLogger(__name__)

class DownloadGnss(arogen.StepGnss):
    
    def __init__(self,out_dir,tmp_dir,log_dir,
                 epoch_range,
                 access,
                 remote_dir,
                 remote_fname,
                 site=None,
                 session=None,
                 site_id=None):
        
        super().__init__(out_dir,tmp_dir,log_dir,
                         epoch_range,
                         site=site,
                         session=session,
                         site_id=site_id)

        self.access = access
        self.remote_dir = remote_dir
        self.remote_fname = remote_fname
                
    def guess_remote_files(self):
        """
        Guess the paths and name of the remote files based on the 
        Session and EpochRange attributes of the DownloadGnss
        
        see also method guess_local_files(), a general method for all 
        StepGnss objects
        """
        
        if not self.remote_fname:
            logger.warning("generic filename empty for %s, the guessed remote filepaths will be wrong",self.session)
        
        hostname_use = self.access['hostname']
        
        rmot_paths_list = []
        
        for epoch in self.epoch_range.epoch_range_list():
            ### guess the potential remote files
            rmot_dir_use = str(self.remote_dir)
            rmot_fname_use = str(self.remote_fname)
            
            rmot_path_use = arodl.join_url(self.access['protocol'],
                                           hostname_use,
                                           rmot_dir_use,
                                           rmot_fname_use)

            rmot_path_use = self.translate_path(rmot_path_use,
                                                epoch)

                                       
            rmot_fname_use = os.path.basename(rmot_path_use)
                                       
            rmot_paths_list.append(rmot_path_use)
            
            iepoch = self.table[self.table['epoch_srt'] == epoch].index[0]
                                            
            self.table.loc[iepoch,'fname']     = rmot_fname_use
            self.table.loc[iepoch,'fpath_inp'] = rmot_path_use
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
            rmot_dir_use = str(self.remote_dir)
            rmot_dir_use = self.translate_path(rmot_dir_use,
                                               epoch)
            rmot_dir_list.append(rmot_dir_use)
            
        rmot_dir_list = sorted(list(set(rmot_dir_list)))
                    
        return rmot_dir_list
    
    def ask_remote_files(self):
        rmot_dir_list = self._guess_remote_directories()
        rmot_files_list = []
        for rmot_dir_use in rmot_dir_list:
            if self.access['protocol'] == "http":
                list_ = arodl.list_remote_files_http(self.access['hostname'],
                                                    rmot_dir_use)
                rmot_files_list = rmot_files_list + list_
            elif self.access['protocol'] == "ftp":
                list_ = arodl.list_remoteo_files_ftp(self.access['hostname'],
                                                   rmot_dir_use,
                                                   self.access['login'],
                                                   self.access['password'])
                rmot_files_list = rmot_files_list + list_
            else:
                logger.error("wrong protocol")
                
            logger.debug("remote files found on rec: %s",list_)
        
        logger.info("nbr remote files found on rec: %s",len(rmot_files_list))
        return rmot_files_list
        
    def check_local_files(self):
        """
        check the existence of the local files, and set the corresponding
        booleans in the ok_out column
        """
        
        local_files_list = []
        
        for irow,row in self.table.iterrows():
            local_file = row['fpath_out']
            if os.path.exists(local_file) and os.path.getsize(local_file) > 0:
                self.table.loc[irow,'ok_out'] = True
                self.table.loc[irow,'size_out'] = os.path.getsize(local_file)
                local_files_list.append(local_file)
            else:
                self.table.loc[irow,'ok_out'] = False
                
        return local_files_list
        
    def invalidate_small_local_files(self,threshold=.80):
        """
        if the local file is smaller than threshold * median 
        of the considered local files in the request table
        the ok_out boolean is set at False, and the local file 
        is redownloaded
        
        check_local_files must be launched 1st
        """
        
        med = self.table['size_out'].median(skipna=True)
        valid_bool = threshold * med < self.table['size_out']
        self.table.loc[:,'ok_out'] = valid_bool
        invalid_local_files_list = list(self.table.loc[valid_bool,'fpath_out'])

        return invalid_local_files_list


    def download_remote_files(self,force_download=False):
        """
        will download locally the files which have been identified by 
        the guess_remote_files method
        
        exploits the fname_remote column of the DownloadGnss.table
        attribute
        """
        download_files_list = []
                
        for irow, row in self.table.iterrows():
            
            epoch = row['epoch_srt']
            rmot_file = row['fpath_inp']
            local_file = row['fpath_out']
                                                                    
            ###### check if the file exists locally
            if row.ok_out == True and not force_download:
                 logger.info("%s already exists locally, skip",
                             os.path.basename(local_file))
                 continue

            ###### use the guessed local file as destination or the generic directory                
            if not local_file: #### the local file has not been guessed
                outdir_use = str(self.out_dir)
                outdir_use = self.translate_path(outdir_use,
                                                 epoch)
            else: #### the local file has been guessed before
                outdir_use = os.path.dirname(local_file)
                
            tmpdir_use = os.path.join(self.tmp_dir,'downloaded')
            
            ###### create the directory if it does not exists
            if not os.path.exists(outdir_use):
                os.makedirs(outdir_use)
            if not os.path.exists(tmpdir_use):
                os.makedirs(tmpdir_use)
            
            ###### download the file            
            if not self.access['protocol'] in ("ftp","http"):
                logger.error("wrong protocol")
                raise Exception
            elif self.access['protocol'] == "http":
                try:
                    file_dl = arodl.download_file_http(rmot_file,
                                                       tmpdir_use)
                    shutil.copy(file_dl,outdir_use)
                    dl_ok = True
                except Exception as e:
                    logger.error("HTTP download error: %s",str(e))
                    dl_ok = False
                    
            elif self.access['protocol'] == "ftp":
                try:
                    file_dl = arodl.download_file_ftp(rmot_file,
                                                      tmpdir_use,
                                                      self.access['login'],
                                                      self.access['password'])
                    shutil.copy(file_dl,outdir_use)
                    dl_ok = True
                except ftplib.error_perm as e:
                    logger.error("FTP download error: %s",str(e))
                    dl_ok = False
                    
            else: ### this case should never happen since there is a protocol test at the begining
                pass

            ###### store the results in the table
            if dl_ok:
                download_files_list.append(file_dl)
                self.table.loc[irow,"ok_out"] = True
                self.table.loc[irow,"fpath_out"] = file_dl
            else:
                self.table.loc[irow,"ok_out"] = False
                
        return download_files_list
