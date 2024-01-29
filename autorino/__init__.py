#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from os import path
import logging.config

#### IMPORT CONFIG FOR LOGGER
log_file_path = os.path.join(path.dirname(path.abspath(__file__)),
                             'config',
                             'logcfg.py')
from . import config
if os.path.isfile(log_file_path):
    ##print("INFO:",log_file_path,"found")
    ###### old config file format
    ###logging.config.fileConfig(fname=log_file_path, disable_existing_loggers=False)
    ###### new dict
    logging.config.dictConfig(config.logcfg.log_config_dict)
else:
    print("ERR:logger config file",log_file_path,"is missing")