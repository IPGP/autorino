#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 25 19:20:22 2024

@author: psakic
"""

import os
import re

from geodezyx import utils


##### Frontend function

def translator(path_inp,translator_dict=None,epoch_inp=None):
    path_translated = str(path_inp)
    path_translated = _translator_env_variables(path_translated)
    if epoch_inp:
        path_translated = _translator_epoch(path_translated,epoch_inp)
    if translator_dict:
        path_translated = _translator_keywords(path_translated,translator_dict)
    return path_translated


##### Internal functions


def _translator_epoch(path_inp,epoch_inp):
    """
    set the correct epoch in path_input string the with the strftime aliases
    https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior
    """
    path_translated = str(path_inp)
    path_translated = epoch_inp.strftime(path_translated)

    #the <HOURCHAR> and <hourchar> alias in a time information,
    #thus must be managed here 

    ichar = epoch_inp.hour
    path_translated = path_translated.replace('<HOURCHAR>',utils.alphabet(ichar).upper()) 
    path_translated = path_translated.replace('<hourchar>',utils.alphabet(ichar).lower()) 

    return path_translated

def _translator_keywords(path_inp,translator_dict):
    path_translated = str(path_inp)
        
    ### replace autorino variable (without a <$....>)
    if re.search('<(?!.*\$).*>',path_translated):    
        for k,v in translator_dict.items():
            path_translated = path_translated.replace("<"+k+">",str(v))
            
    return path_translated


def _translator_env_variables(path_inp):
    path_translated = str(path_inp)
    
    ### replace system envionnemt variables
    if re.search('<\$.*>',path_translated):
        for k,v in os.environ.items():
            path_translated = path_translated.replace("<$"+k+">",str(v))
    
    return path_translated


