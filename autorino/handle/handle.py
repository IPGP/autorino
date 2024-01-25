#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 15:00:40 2024

@author: psakic
"""

import autorino.general  as arogen

# Create a logger object.
import logging
logger = logging.getLogger(__name__)

class HandleGnss(arogen.StepGnss):
    def __init__(self,session,epoch_range,out_dir):
        super().__init__(session,epoch_range,out_dir)
        
