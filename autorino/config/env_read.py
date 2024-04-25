#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 22/04/2024 16:16:23

@author: psakic
"""
import os
import yaml

# Create a logger object.
import logging
logger = logging.getLogger(__name__)

def read_env(envfile_path=None):
    """
    read a environement config file path (YAML format) and return
    the corresponding dictionnary

    priority for envfile path :
    fct argument > bashrc env variable > default in the current file
    """

    envfile_path_def = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "autorino_env_default.yml")

    if envfile_path:
        logger.debug("load environement config file: %s",
                     envfile_path)
        envfile_path_use = envfile_path
    elif 'AUTORINO_ENV' in os.environ:
        envfile_path_use = os.environ['AUTORINO_ENV']
    else:
        envfile_path_use = envfile_path_def

    if not os.path.isfile(envfile_path_use):
        logger.warning("environement config file not found, fallback to default values: %s",
                       envfile_path_use)
        envfile_path_use = envfile_path_def

    y_dic = yaml.safe_load(open(envfile_path_use))

    return y_dic



