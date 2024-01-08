#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  8 16:53:51 2024

@author: psakicki
"""

#### Import the logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel("INFO")

class WorkflowGnss():
    
    def print_table(self,silent=False,max_colwidth=20):
        form = dict()
        form['fraw'] = lambda x: x[-max_colwidth-1:]
        str_out = self.table.to_string(max_colwidth=max_colwidth,
                                       formatters=form)
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


