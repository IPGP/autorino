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
import mergedeep
import autorino
import rinexmod

### we need to clear the root logger to avoid duplicate logs
root_logger = logging.getLogger()
root_logger.handlers.clear()  # Clear all handlers in the root logger

logger = logging.getLogger("autorino")
logger.setLevel("DEBUG")


def read_env(envfile_path=None):
    """
    Reads an environment configuration file (YAML format) and returns the corresponding dictionary.

    Priority for determining the environment file path:
    1. Function argument
    2. Environment variable `AUTORINO_ENV`
    3. Default file in the current directory
    """

    varo = autorino.__version__
    vrimo = rinexmod.__version__
    logger.info("autorino & rinexmod version: %s & %s", varo, vrimo)

    # Default environment file path
    default_env_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "autorino_env_default.yml"
    )

    # Determine the environment file path
    envfile_path_use = (
        envfile_path or os.environ.get("AUTORINO_ENV", "")
    )

    if not envfile_path_use or not os.path.exists(envfile_path_use):
        logger.warning(
            f"{'Custom environment configfile not defined' if not envfile_path_use else f'File not found: {envfile_path_use}'}"
        )
        logger.warning("Falling back to default values in %s", default_env_path)
        envfile_path_use = default_env_path

    logger.info("Loading environment configfile: %s", envfile_path_use)

    # Load and merge environment configurations
    env_default = yaml.safe_load(open(default_env_path))["environment"]
    env_custom = yaml.safe_load(open(envfile_path_use))["environment"]
    return mergedeep.merge({}, env_default, env_custom)

# Global environment dictionary used throughout the package
ARO_ENV_DIC = read_env()