#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 15:47:05 2022

@author: psakicki
"""

#### Import star style
from geodezyx import *                   # Import the GeodeZYX modules
from geodezyx.externlib import *         # Import the external modules
from geodezyx.megalib.megalib import *   # Import the legacy modules names

import yaml 

p1 = "/home/psakicki/CODES/IPGP/autorino/configfiles/proto_config01a.yml"
p2 = "/home/psakicki/CODES/IPGP/autorino/configfiles/minimal_exemple.yml"

Y1 = yaml.safe_load(open(p1))
Y2 = yaml.safe_load(open(p2))