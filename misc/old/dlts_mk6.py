import datetime as dt
import pandas as pd
import numpy as np
import os
from autorino import download as ardl
from autorino import configread as arcfg

import yaml


###########################################################################################


pconfig = "/home/gps/tests_pierres/autorino/configfiles/proto_config_HOUE_03a.yml"
pconfig = "/home/gps/tests_pierres/autorino/configfiles/proto_config_PSA1_03a.yml"

Y1 = yaml.safe_load(open(pconfig))

SESlist, REQlist = arcfg.session_request_from_configfile(pconfig)
REQ = REQlist[1]
#REQ = REQlist

#L = REQ.ask_remote_files()
L = REQ.guess_remote_local_files(guess_local=1)
L = REQ.check_local_files()
L = REQ.invalidate_small_local_files()

print(REQ.req_table.to_string())

REQ.download_remote_files()
print(REQ.req_table.to_string())
