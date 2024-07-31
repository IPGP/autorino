#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging.config
import os
from os import path

#### IMPORT CONFIG FOR LOGGER
log_file_path = os.path.join(path.dirname(path.abspath(__file__)),
                             'logcfg',
                             'logcfg.py')
from . import logcfg
if os.path.isfile(log_file_path):
    logging.config.dictConfig(logcfg.log_config_dict)
else:
    print("ERR:logger config file",log_file_path,"is missing")
