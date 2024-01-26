import datetime as dt
import pandas as pd
import numpy as np
import os
from autorino import download as arodl
from autorino import convert as arocnv
from autorino import general as arogen
from autorino import configread as arocfg

import yaml


###########################################################################################
## dummy comment
pcfg = '/home/sysop/pymods_ovs/autorino/configfiles/proto_config_06b_CFNG.yml'

tupout = arocfg.read_configfile(pcfg)

workflow_lis, y_site, y_device, y_access = tupout
dwl = workflow_lis[0]
cnv = workflow_lis[1]

#L = REQ.ask_remote_files()
L = dwl.guess_local_files()
L = dwl.guess_remote_files()
L = dwl.check_local_files()
L = dwl.invalidate_small_local_files()

dwl.print_table()
dwl.download_remote_files()
dwl.print_table()

cnv.load_table_from_prev_step_table(dwl.table)

cnv.print_table()
cnv.convert_rnxmod()

