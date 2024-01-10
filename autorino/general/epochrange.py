#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  8 15:47:58 2024

@author: psakicki
"""

#### Import star style
import dateparser
import pandas as pd
import numpy as np

def dateparser_frontend(date_in,tz="UTC"):
    """
    Frontend function to parse a string/datetime 
    to a Pandas Timestamp 
    (standard used for the DownloadGnss object)
    Also apply a timezone (UTC per default)
    
    NB: the rounding will not take place here
    rounding is not a parsing operation
    """
    if type(date_in) is str:
        date_out = pd.Timestamp(dateparser.parse(date_in))
    else:
        date_out = pd.Timestamp(date_in)
    
    if not date_out.tz:
        date_out = pd.Timestamp(date_out, tz=tz)
    
    return date_out
    
def dateround_frontend(date_in,period,round_method="ceil"):
    """    
    Frontend function to round a Pandas Timestamp 
    according to the "ceil", "floor" or "round" approach
    """
    if round_method == "ceil":
        date_out = date_in.ceil(period)
    elif round_method == "floor":
        date_out = date_in.floor(period)        
    elif round_method == "round":
        date_out = date_in.ceil(period)
    else:
        raise Exception
        
    return date_out
        

class EpochRange:
    def __init__(self,epoch1,epoch2,
                 period="01D",
                 round_method="ceil",
                 tz="UTC"):
        self.period = period
        #see also self.period_values, the period int and str values
        self.round_method = round_method
        self.tz = tz

        self._epoch1_raw = epoch1
        self._epoch2_raw = epoch2
    
        _epoch1tmp = dateparser_frontend(self._epoch1_raw)
        _epoch2tmp = dateparser_frontend(self._epoch2_raw)
        _epoch_min_tmp = np.min((_epoch1tmp,_epoch2tmp))
        _epoch_max_tmp = np.max((_epoch1tmp,_epoch2tmp))
        
        self.epoch_start = _epoch_min_tmp  ### setter bellow
        self.epoch_end   = _epoch_max_tmp  ### setter bellow

    def __repr__(self):
        return "epoch range from {} to {}, period {}".format(self.epoch_start,
                                                             self.epoch_end,
                                                             self.period)
    
    ############ getters and setters 
    @property
    def epoch_start(self):
        return self._epoch_start
    @epoch_start.setter
    def epoch_start(self,value):
        self._epoch_start = dateparser_frontend(value,tz=self.tz)
        self._epoch_start = dateround_frontend(self._epoch_start,
                                               self.period,
                                               self.round_method) 
    @property
    def epoch_end(self):
        return self._epoch_end
    @epoch_end.setter
    def epoch_end(self,value):
        self._epoch_end = dateparser_frontend(value) #,tz=self.tz) 
        self._epoch_end = dateround_frontend(self._epoch_end,
                                             self.period,
                                             self.round_method)
    @property
    def period_values(self):
        return int(self.period[:-1]), str(self.period[-1])
                                             
    
    ########### methods
    def epoch_range_list(self,end_bound=False):
        if not end_bound: ### start bound
            epochrange_srt=pd.date_range(self.epoch_start,
                                         self.epoch_end,
                                         freq=self.period)
            epochrange = epochrange_srt
        else: ### end bound
            plus_one = np.timedelta64(*self.period_values)
            epochrange_end=pd.date_range(self.epoch_start,
                                         self.epoch_end+plus_one,
                                         freq=self.period)
            epochrange = epochrange_end[1:] - np.timedelta64(1,'s')
            

        return list(epochrange)
