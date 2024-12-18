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
import geodezyx.conv as conv



spc = arohdl.SpliceGnss(dir,
                        dir,
                        dir,
                        epoch_range=(conv.doy2dt(2024,226),
                                     conv.doy2dt(2024,227),
                                     "1d"),
                                     inp_dir=prnx)

rnxsinp = spc.find_local_inp(return_as_step_obj=True)

spc.splice("given",rnxsinp)


import versioningit
versioningit.get_version('/home/psakicki/CODES/IPGP/autorino')
