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
logger = logging.getLogger(__name__)
logger.setLevel("INFO")

class WorkflowGnss():
    
    def __init__(self,session,epoch_range,out_dir):
        self.session = session
        self.epoch_range = epoch_range ### setter bellow
        self.out_dir = out_dir
        self.tmp_dir = session.tmp_dir
        self.table = self._table_init()
    
    def print_table(self,silent=False,max_colwidth=33):
        
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

        str_out = self.table.to_string(max_colwidth=max_colwidth+1,
                                       formatters=form)
                                       ### add +1 in max_colwidth for safety
        if not silent:
            name = type(self).__name__
            logger.info("%s %s/%s\n%s",name,
                                       self.session.site,
                                       self.epoch_range,
                                       str_out)
        return str_out
        
    ######## getter and setter 
    @property
    def epoch_range(self):
        return self._epoch_range
        
    @epoch_range.setter
    def epoch_range(self,value):
        self._epoch_range = value
        if self._epoch_range.period != self.session.session_period:  
            logger.warn("Session period (%s) != Epoch Range period (%s)",
            self.session.session_period,self._epoch_range.period)

    ######## internal methods 
    def _table_init(self,
                    table_cols=['fname',
                                'site',
                                'epoch',
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
            df['epoch'] = self.epoch_range.epoch_range_list()
        
        return df

