#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07/04/2025 15:01:05

@author: psakic
"""

import logging.config
import os
from os import path

__version__ = "2.4.0"  #  changed automaticcaly with bump-my-version

#### IMPORT CONFIG FOR LOGGER
log_file_path = os.path.join(
    path.dirname(path.abspath(__file__)), "cfglog", "cfglog.py"
)

if os.path.isfile(log_file_path):
    from . import cfglog

    logging.config.dictConfig(cfglog.log_config_dict)
else:
    print("ERR:logger cfgfiles file", log_file_path, "is missing")


#### IMPORT AUTORINO INTERNAL SUBMODULES
from . import api
from . import bin

# from . import cfgenv
# from . import cfgfiles
# from . import cfglog
# from . import check
# from . import common
# from . import convert
# from . import download
# from . import handle

__all__ = [
    "api",
    "bin",
    # 'cfgenv',
    # 'cfgfiles',
    # 'cfglog',
    # 'check',
    # 'common',
    # 'convert',
    # 'download',
    # 'handle'
]

if __name__ == "__main__":
    print("autorino version", __version__)
    print("autorino.__all__", __all__)
