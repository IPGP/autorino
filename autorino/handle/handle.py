#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 15:00:40 2024

@author: psakic
"""

import autorino.common as arocmn
import autorino.convert as arocnv

# Create a logger object.
import logging
logger = logging.getLogger(__name__)

class HandleGnss(arocmn.StepGnss):
    def __init__(self,out_dir,tmp_dir,log_dir,
                 epoch_range,
                 site=None,
                 session=None):
    
        super().__init__(out_dir,tmp_dir,log_dir,
                         epoch_range,
                         site=site,
                         session=session)

    def splice(self):
        ### divide_step_by_epochs will create several HandleGnss objects
        hdl_objs_lis = self.divide_step_by_epochs()
        
        for hdl in hdl_objs_lis:
            hdl._splice_mono()
        
    def _splice_mono(self):
        #### add a test here to be sure that only one epoch is inside
        fpath_inp_lst = list(self.table['fpath_inp'])
        
        tmp_dir_use = self.translate_path(self.tmp_dir)

        handle_software = 'converto'
        if handle_software == 'converto':
            frnxtmp, _ = arocnv.converter_run(fpath_inp_lst,
                                              tmp_dir_use,
                                              'converto',
                                              bin_options=['-cat'])
        elif handle_software == 'gfzrnx':
            frnxtmp, _ = arocnv.converter_run(fpath_inp_lst,
                                              tmp_dir_use,
                                              'gfzrnx',
                                              bin_options=['-f'])


        self.
        


    # def find_rnx_

    # def split(self):

    
            
    

        
