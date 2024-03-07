import datetime as dt
import pandas as pd
import numpy as np
import os
from autorino import download as arodl
from autorino import convert as arocnv
from autorino import general as arogen
from autorino import config as arocfg

import yaml


###############################################################################
## dummy comment2
pcfg = '/home/sysop/pymods_ovs/autorino/configfiles/proto_config_06d_CFNG.yml'

tup_out = arocfg.read_cfg(pcfg)
workflow_lis, y_site, y_device, y_access = tup_out
arocfg.run_workflow(workflow_lis)

