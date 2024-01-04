import datetime as dt
import pandas as pd
import numpy as np
import os
from autorino import download as arodl
from autorino import configread as arocfg

import yaml


###########################################################################################

pconfig='/home/sysop/pymods_ovs/autorino/configfiles/proto_config_05b_BOMG.yml'
pconfig='/home/sysop/pymods_ovs/autorino/configfiles/proto_config_05c_BOMG.yml'

Y1 = yaml.safe_load(open(pconfig))

ses_lst, req_lst = arocfg.session_request_from_configfile(pconfig)
#REQ = REQlist[1]
req = req_lst

#L = REQ.ask_remote_files()
L = req.guess_remote_local_files(guess_local=1)
L = req.check_local_files()
L = req.invalidate_small_local_files()

print(req.table.to_string())

req.download_remote_files()
print(req.table.to_string())
