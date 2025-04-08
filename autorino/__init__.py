#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07/04/2025 15:01:05

@author: psakic
"""

#### IMPORT AUTORINO INTERNAL SUBMODULES
from . import api
from . import bin
from . import cfgenv
from . import cfgfiles
from . import cfglog
from . import check
from . import common
from . import convert
from . import download
from . import handle

__all__ = ['api',
           'bin',
           'cfgenv',
           'cfgfiles',
           'cfglog',
           'check',
           'common',
           'convert',
           'download',
           'handle']

if __name__ == '__main__':
    print("autorino version",__version__)
    print("autorino.__all__",__all__)
