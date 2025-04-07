#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07/04/2025 15:01:05

@author: psakic
"""

import logging.config
import os
from os import path
import json

__version__='1.2.0' # changed automaticcaly with bump-my-version

#### IMPORT CONFIG FOR LOGGER
log_json_path = os.path.join(
    path.dirname(path.abspath(__file__)), "cfglog", "cfglog.json"
)

if os.path.isfile(log_json_path):
    with open(log_json_path) as f:
        json_config = json.load(f)
    logging.config.dictConfig(json_config)
else:
    print("ERR:logger cfgfiles file", log_json_path, "is missing")

#### IMPORT AUTORINO INTERNAL SUBMODULES
# necessary for frontend CLI programs
from . import api
from . import bin