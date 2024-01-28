#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 15:00:40 2024

@author: psakic
"""

import autorino.general as arogen
import autorino.convert as arocnv

from rinexmod import rinexfile

# Create a logger object.
import logging
logger = logging.getLogger(__name__)

class HandleGnss(arogen.StepGnss):       
    def __init__(self,out_dir,tmp_dir,log_dir,
                 epoch_range,
                 site=None,
                 session=None,
                 site_id=None):
    
        super().__init__(out_dir,tmp_dir,log_dir,
                         epoch_range,
                         site=site,
                         session=session,
                         site_id=site_id)

    def splice(self):
        
        hdl_obj_out = self.divide_step_by_epochs()
        
        for hdl in hdl_obj_out:
            hdl._splice_mono()
        
    def _splice_mono(self):
        #### add a test here to be sure that only one epoch is inside
        fpath_inp_lst = list(self.table['fpath_inp'])
        
        tmp_dir_use = self.translate_path(self.tmp_dir)
        
        frnxtmp, _ = arocnv.converter_run(fpath_inp_lst,
                                          tmp_dir_use,
                                          'converto',
                                          bin_options=['-cat'])
        
        # frnxtmp, _ = arocnv.converter_run(fpath_inp_lst,
        #                                   tmp_dir_use,
        #                                   'converto',
        #                                   bin_options=['-cat'])
        

tmp_dir = '/home/psakicki/autorino_workflow_tests/temp'
out_dir = '/home/psakicki/autorino_workflow_tests/handle'
log_dir = tmp_dir

epo = arogen.epochrange.create_dummy_epochrange()
hdl = HandleGnss(out_dir, tmp_dir, log_dir, epo, site_id='CFNG')



from geodezyx import utils

p="/home/psakicki/autorino_workflow_tests/conv_tests/CFNG00REU/2024/024"
L = utils.find_recursive(p,"*rnx")


hdl.load_table_from_filelist(L)
hdl.update_epoch_table_cols_from_fname()

hdl.splice()

        

        
