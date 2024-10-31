# import datetime as dt
# import pandas as pd
# import numpy as np
# import os
# from autorino import download as arodwl
# from autorino import convert as arocnv
# from autorino import general as arocmn
import yaml

from autorino import cfgfiles as arocfg

###########################################################################################

pconfig='/home/sysop/pymods_ovs/autorino/configfiles/proto_config_05b_BOMG.yml'
pconfig='/home/sysop/pymods_ovs/autorino/configfiles/proto_config_05c_BOMG.yml'
pconfig='/home/psakicki/CODES/IPGP/autorino/configfiles/proto_config_05c_RVAG.yml'
pconfig='/home/psakicki/CODES/IPGP/autorino/configfiles/proto_config_05d_RVAG_dummy_on_tpx1.yml'

Y1 = yaml.safe_load(open(pconfig))

ses_lst, dwl_lst = arocfg.session_download_from_configfile(pconfig)
dwl = dwl_lst[0]
ses = ses_lst[0]
#req = req_lst

#L = REQ.ask_remote_raw()
L = dwl.guess_remote_files()
L = dwl.guess_local_files()
L = dwl.check_local_files()
L = dwl.invalidate_small_local_files()

dwl.print_table()

    


# dwl.download_remote_files()
# dwl.verbose()

# out = "/home/sysop/workflow_tests/convert_tests"
# sitelog_dir = '/home/sysop/metadata/OVPF'

# conv = arocnv.ConvertGnss(ses,dwl.epoch_range_inp,out,sitelog_dir)

# conv.load_tab_prev_tab(dwl.table)
# conv.verbose()
# conv.conv_rnxmod_files()
# conv.verbose()
