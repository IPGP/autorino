#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import logging.config
import os
from os import path

#### IMPORT CONFIG FOR LOGGER
log_file_path = os.path.join(path.dirname(path.abspath(__file__)),
                             'cfglog',
                             'cfglog.py')
from . import cfglog

if os.path.isfile(log_file_path):
    logging.config.dictConfig(cfglog.log_config_dict)

else:
    print("ERR:logger cfgfiles file",log_file_path,"is missing")
