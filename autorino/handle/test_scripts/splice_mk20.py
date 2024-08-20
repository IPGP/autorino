#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 19/08/2024 18:26:29

@author: psakic
"""


prnx = "/home/psakicki/aaa_FOURBI/RINEXexemple/SOUF00GLP/%Y/%j"
rnxstruct = ""
dir = "/home/psakicki/aaa_FOURBI/test_splice_SOUF"

import autorino.handle as arohdl

import datetime as dt
import geodezyx.conv as conv


spc = arohdl.SpliceGnss(dir,
                        dir,
                        dir,
                        epoch_range=(conv.doy2dt(2024,226),
                                     conv.doy2dt(2024,227),
                                     "1d"),
                                     inp_dir_parent=prnx,
                                     inp_structure=rnxstruct)



#spc.find_local_inp(return_as_step_obj=True).print_table()

spc.splice(spc.find_local_inp(return_as_step_obj=True))
#spc.feed_by_epochs(spc.find_local_inp(return_as_step_obj=True))
