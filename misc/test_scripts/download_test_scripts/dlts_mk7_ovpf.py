from autorino import convert as arocnv
import yaml

from autorino import configread as arocfg
from autorino import convert as arocnv

###########################################################################################

pconfig='/home/sysop/pymods_ovs/autorino/configfiles/proto_config_05b_BOMG.yml'
pconfig='/home/sysop/pymods_ovs/autorino/configfiles/proto_config_05c_BOMG.yml'
pconfig='/home/sysop/pymods_ovs/autorino/configfiles/proto_config_05c_RVAG.yml'
pconfig='/home/sysop/pymods_ovs/autorino/configfiles/proto_config_05d_CNFG.yml'

Y1 = yaml.safe_load(open(pconfig))

ses_lst, dwl_lst = arocfg.session_download_from_configfile(pconfig)
dwl = dwl_lst[0]
ses = ses_lst[0]
#req = req_lst

#L = REQ.ask_remote_raw()
L = dwl.guess_local_files()
L = dwl.guess_remote_files()
L = dwl.check_local_files()
L = dwl.invalidate_small_local_files()

dwl.print_table()
dwl.download_remote_files()
dwl.print_table()

out = "/home/sysop/workflow_tests/convert_tests"
sitelog_dir = '/home/sysop/metadata/OVPF'

conv = arocnv.ConvertGnss(ses, dwl.epoch_range, out, sitelog_dir)

conv.load_tab_prev_tab(dwl.table)
conv.print_table()
conv.convert()
conv.print_table()
