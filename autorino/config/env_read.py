#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 22/04/2024 16:16:23

@author: psakic
"""
import os
import yaml

def read_env(envfile_path=None):

    envfile_path_def = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    'autorino_env_default.yml')
    if not envfile_path:
        envfile_path_use = envfile_path_def
    elif not os.path.isfile(envfile_path):
        envfile_path_use = envfile_path_def
    else:
        envfile_path_use = envfile_path

    y = yaml.safe_load(open(envfile_path_use))

    return y



