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
import re

class EpochRange:
    def __init__(self,epoch1,epoch2,
                 period="1d",
                 round_method="floor",
                 tz="UTC"):
        """
        period : str, optional
            the rounding period. 
            Use the pandas' frequency aliases convention (see bellow for details).
            
        Note
        ----
        Pandas' frequency aliases memo
        https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases
        """
        
        
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
        self._epoch_start = _round_date(self._epoch_start,
                                               self.period,
                                               self.round_method) 
    @property
    def epoch_end(self):
        return self._epoch_end
    @epoch_end.setter
    def epoch_end(self,value):
        self._epoch_end = dateparser_frontend(value) #,tz=self.tz) 
        self._epoch_end = _round_date(self._epoch_end,
                                             self.period,
                                             self.round_method)
    @property
    def period_values(self):
        numbers = re.findall(r'[0-9]+', self.period)
        alphabets = re.findall(r'[a-zA-Z]+', self.period)
        val = int("".join(*numbers))
        unit = str("".join(*alphabets))
        return val,unit
                                             
    
    ########### methods
    def epoch_range_list(self,end_bound=False):
        if not end_bound: ### start bound
            epochrange_srt=pd.date_range(self.epoch_start,
                                         self.epoch_end,
                                         freq=self.period)
            epochrange = epochrange_srt
        else: ### end bound
            plus_one = pd.Timedelta(self.period)
            epochrange_end=pd.date_range(self.epoch_start,
                                         self.epoch_end+plus_one,
                                         freq=self.period)
            epochrange = epochrange_end[1:] - np.timedelta64(1,'s')
            

        return list(epochrange)

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
    
def _round_date(date_in,period,round_method="floor"):
    """
    low-level function to round a Pandas Serie or a datetime-like object 
    according to the "ceil", "floor" or "round" approach

    Parameters
    ----------
    date_in : Pandas Serie or a datetime-like object 
        Input date .
    period : str, optional
        the rounding period. 
        Use the pandas' frequency aliases convention (see bellow for details).
    round_method : str, optional
        round method: 'ceil', 'floor', 'round'. The default is "floor".

    Returns
    -------
    date_out : Pandas Serie or datetime-like object (same as input)
        rounded date.

    Note
    ----
    Pandas' frequency aliases memo
    https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases
    
    """
    
    # we separate the Series case of the simple datetime-like 
    # both for ease and performance reason
    
    if type(date_in) is pd.Series:
        
        date_use = date_in
        
        if round_method == "ceil":
            date_out = date_use.dt.ceil(period)
        elif round_method == "floor":
            date_out = date_use.dt.floor(period)        
        elif round_method == "round":
            date_out = date_use.dt.round(period)
        else:
            raise Exception
        
    else:
        date_typ = type(date_in)
        date_use = pd.Timestamp(date_in)
    
        if round_method == "ceil":
            date_out = date_use.ceil(period)
        elif round_method == "floor":
            date_out = date_use.floor(period)        
        elif round_method == "round":
            date_out = date_use.round(period)
        else:
            raise Exception
        
        date_out = date_typ(date_out)
        
    return date_out
        

def round_epochs(epochs_inp,
                 period = '1d',
                 rolling_period=False,
                 rolling_ref=-1,
                 round_method = 'floor'):
    """
    High-levelfunction to round several epochs to a common one.
    Useful to group and then splice RINEX
    
    Use it with pandas .groupby in a further step

    Parameters
    ----------
    epochs_inp : iterable
        The input epochs expected to be rounded.
    period : str, optional
        the rounding period. 
        Use the pandas' frequency aliases convention (see bellow for details).
        The default is '1d'.
    rolling_period : bool, optional
        The rounding depends on a referece epoch definied with rolling_ref.
        The default is False.
    rolling_ref : datetime-like or int, optional
        If datetime-like object, use this epoch as reference.
        If integer, use the epoch of the corresponding index  
        Use -1 for the last epoch for instance.
        The default is -1.
    round_method : str, optional
        round method: 'ceil', 'floor', 'round'. The default is "floor".

    Returns
    -------
    epochs_rnd : 
        Pandas Serie of Timestamp or Timedelta 
    
    Note
    ----
    Pandas' frequency aliases memo
    https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases
    
    """

    
    epochs_use = pd.Series(epochs_inp)
    
    if not rolling_period:
        epochs_rnd = _round_date(epochs_use,period,round_method)
    else:
        if type(rolling_ref) is int:
            rolling_ref_use = epochs_use.iloc[rolling_ref]
        else:
            rolling_ref_use = rolling_ref
        
        ### add one second to be sure that the rolling_ref is included in a group
        rolling_ref_use = rolling_ref_use + np.timedelta64(1,'s')
        
        roll_diff = epochs_use - rolling_ref_use
        epochs_rnd = _round_date(roll_diff,period,round_method)
        
    return epochs_rnd        
        

def create_dummy_epochrange():
    """
    Create a fake/dummy EpochRange object
    for test/developpement purpose

    Returns
    -------
    ses : EpochRange object
        dummy EpochRange object.

    """
    
    epo = EpochRange(epoch1="24 hours and 30min ago",
                     epoch2="30 min ago",
                     period='15min')
    return epo

