#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#import logging
import logging.config
import os
from os import path
import json

__version__='1.2.0' # changed automaticcaly with bump-my-version

#### IMPORT CONFIG FOR LOGGER
log_file_path = os.path.join(
    path.dirname(path.abspath(__file__)), "cfglog", "cfglog.py"
)

log_json_path = os.path.join(
    path.dirname(path.abspath(__file__)), "cfglog", "cfglog.json"
)

#from . import cfglog

if os.path.isfile(log_json_path):
    with open(log_json_path) as f:
        json_config = json.load(f)
    logging.config.dictConfig(json_config)
else:
    print("ERR:logger cfgfiles file", log_file_path, "is missing")

# if os.path.isfile(log_file_path):
#     logging.config.dictConfig(cfglog.log_config_dict)
#     #from .cfglog import log_config_dict
#     #logging.config.dictConfig(log_config_dict)
# else:
#     print("ERR:logger cfgfiles file", log_file_path, "is missing")

#### IMPORT AUTORINO INTERNAL SUBMODULES
# from autorino import api
# from . import bin