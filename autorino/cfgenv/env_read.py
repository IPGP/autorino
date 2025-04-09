#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 22/04/2024 16:16:23

@author: psakic
"""
# Create a logger object.
import logging
import os
import collections.abc
import yaml
from pathlib import Path



### we need to clear the root logger to avoid duplicate logs
root_logger = logging.getLogger()
root_logger.handlers.clear()  # Clear all handlers in the root logger

logger = logging.getLogger('autorino')
logger.setLevel("DEBUG")

def update_recursive(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update_recursive(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def load_bashrc_vars():
    bashrc = Path.home() / '.bashrc'

    environ_out = os.environ.copy()

    if bashrc.exists():
        # Simple parsing - may need more robust solution
        exports = [line for line in bashrc.read_text().splitlines()
                  if line.startswith('export ')]
        for export in exports:
            var, value = export[7:].split('=', 1)
            if not var in environ_out.keys():
                environ_out[var] = value.strip('"\'')

        return environ_out

def read_env(envfile_path=None):
    """
    read a environement cfgfiles file path (YAML format) and return
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

    environ_use = load_bashrc_vars()
    print(environ_use)

    # Determine the environment file path based on the function argument,
    # environment variable, or default to an empty string
    if envfile_path:
        envfile_path_use = envfile_path
    elif "AUTORINO_ENV" in environ_use.keys():
        envfile_path_use = environ_use["AUTORINO_ENV"]
    else:
        envfile_path_use = ""

    # Check if the specified environment file exists, otherwise fallback to the default file
    if not os.path.isfile(envfile_path_use) or envfile_path_use == "":
        if envfile_path_use == "":
            logger.warning(
                "custom environment configfile not defined in the environment variable $AUTORINO_ENV"
            )
        else:
            logger.warning(
                "$AUTORINO_ENV custom environment configfile not found in %s", envfile_path_use
            )

        logger.warning("fallback to default values in %s", envfile_path_def)
        envfile_path_use = envfile_path_def

    # Log the path of the environment file being loaded
    logger.info("load environment configfile: %s", envfile_path_use)

    # Load the default and specified environment files and merge their contents
    env_dic_def = yaml.safe_load(open(envfile_path_def))
    env_dic_use = yaml.safe_load(open(envfile_path_use))

    env_dic_fin = env_dic_def.copy()
    env_dic_fin = update_recursive(env_dic_fin, env_dic_use)
    #logger.debug("default environment values (%s): %s", envfile_path_def, env_dic_def)
    #logger.debug("used environment values (%s): %s", envfile_path_use, env_dic_use)
    #logger.debug("final environment values: %s", env_dic_fin)

    # Return the merged dictionary
    return env_dic_fin


aro_env_dict = read_env()


