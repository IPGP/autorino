#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  8 16:53:51 2024

@author: psakic
"""

import logging
import os
import re

import numpy as np

from geodezyx import utils

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

def create_dummy_site_dic():
    d = dict()

    d['name'] = 'XXXX'
    d['site_id'] = 'XXXX00XXX'
    d['domes'] = '00000X000'
    d['sitelog_path'] = '/null'
    d['position_xyz'] = (6378000, 0, 0)

    return d


def create_dummy_session_dic():
    d = dict()

    d['name'] = 'NA'
    d['data_frequency'] = "30S"
    d['tmp_dir_parent'] = '<$HOME>/autorino_workflow_tests/tmp'
    d['tmp_dir_structure'] = '<site_id9>/%Y/%j'
    d['log_parent_dir'] = '<$HOME>/autorino_workflow_tests/log'
    d['log_dir_structure'] = '<site_id9>/%Y/%j'
    d['out_dir_parent'] = '<$HOME>/autorino_workflow_tests/out'
    d['out_dir_structure'] = '<site_id9>/%Y/%j'

    return d


def input_list_interpret(inp_fil, inp_regex=".*"):
    """
    Handles multiple types of input lists (in a general sense)
    and returns a python list of the input

    inp_fil can be:
        * a python list (then nothing is done)
        * a text file path containing a list of files (read as a python list)
        * a tuple containing several text files path  (recursive version of the previous point)
        * a directory path (all the files matching inp_regex are read)
    """

    if not inp_fil:
        flist = []
    elif isinstance(inp_fil, tuple) and os.path.isfile(inp_fil[0]):
        flist = list(np.hstack([open(f, "r+").readlines() for f in inp_fil]))
        flist = [f.strip() for f in flist]
    elif isinstance(inp_fil, list):
        flist = inp_fil
    elif os.path.isfile(inp_fil):
        flist = open(inp_fil, "r+").readlines()
        flist = [f.strip() for f in flist]
    elif os.path.isdir(inp_fil):
        flist = utils.find_recursive(inp_fil,
                                     inp_regex,
                                     case_sensitive=False)
    else:
        flist = []
        logger.warning("the filelist is empty")

    if inp_regex != ".*":
        flist = [f for f in flist if re.match(inp_regex, f)]

    return flist
