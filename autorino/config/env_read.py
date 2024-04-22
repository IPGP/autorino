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
    """

    envfile_path_def = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "autorino_env_default.yml")
    if not envfile_path:
        envfile_path_use = envfile_path_def
    elif not os.path.isfile(envfile_path):
        logger.warning("environement config file not found, fallback to default values: %s",
                       envfile_path)
        envfile_path_use = envfile_path_def
    else:
        logger.debug("load environement config file: %s",
                     envfile_path)
        envfile_path_use = envfile_path

    y_dic = yaml.safe_load(open(envfile_path_use))

    return y_dic



