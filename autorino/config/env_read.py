#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 22/04/2024 16:16:23

@author: psakic
"""
# Create a logger object.
import logging
import os

import yaml

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")


def read_env(envfile_path=None):
    """
    read a environement config file path (YAML format) and return
    the corresponding dictionnary

    priority for envfile path :
    fct argument > bashrc env variable > default in the current file
    """

    envfile_path_def = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "autorino_env_default.yml")

    envfile_path_use = None

    if envfile_path:
        envfile_path_use = envfile_path
    elif 'AUTORINO_ENV' in os.environ:
        envfile_path_use = os.environ['AUTORINO_ENV']
    else:
        envfile_path_use = ""

    if not os.path.isfile(envfile_path_use) or envfile_path_use == "":
        if envfile_path_use == "":
            logger.warning("custom environement config file not defined in the environnement variable AUTORINO_ENV")
        else:
            logger.warning("custom environement config file not found in %s",envfile_path_use)

        logger.warning("fallback to default values in %s",envfile_path_def)
        envfile_path_use = envfile_path_def

    logger.debug("load environement config file: %s",envfile_path_use)

    y_dic = yaml.safe_load(open(envfile_path_use))

    return y_dic



