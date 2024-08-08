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

    # Set the default path for the environment file
    envfile_path_def = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "autorino_env_default.yml"
    )

    # Initialize the variable to hold the path to the environment file to be used
    envfile_path_use = None

    # Determine the environment file path based on the function argument,
    # environment variable, or default to an empty string
    if envfile_path:
        envfile_path_use = envfile_path
    elif "AUTORINO_ENV" in os.environ:
        envfile_path_use = os.environ["AUTORINO_ENV"]
    else:
        envfile_path_use = ""

    # Check if the specified environment file exists, otherwise fallback to the default file
    if not os.path.isfile(envfile_path_use) or envfile_path_use == "":
        if envfile_path_use == "":
            logger.warning(
                "custom environment config file not defined in the environment variable AUTORINO_ENV"
            )
        else:
            logger.warning(
                "custom environment config file not found in %s", envfile_path_use
            )

        logger.warning("fallback to default values in %s", envfile_path_def)
        envfile_path_use = envfile_path_def

    # Log the path of the environment file being loaded
    logger.info("load environment config file: %s", envfile_path_use)

    # Load the default and specified environment files and merge their contents
    env_dic_def = yaml.safe_load(open(envfile_path_def))
    env_dic_use = yaml.safe_load(open(envfile_path_use))

    env_dic_fin = env_dic_use.copy()
    env_dic_fin.update(env_dic_def)

    logger.debug("environment values: %s", env_dic_fin)

    # Return the merged dictionary
    return env_dic_fin


aro_env_dict = read_env()
