from autorino import cfgfiles as arocfg

###########################################################################################
## dummy comment2
pcfg = '/home/sysop/pymods_ovs/autorino/configfiles/proto_config_06d_CFNG.yml'

tupout = arocfg.read_cfg(pcfg)

workflow_lis, y_site, y_device, y_access = tupout
dwl = workflow_lis[0]
cnv = workflow_lis[1]

#L = REQ.ask_remote_raw()
L = dwl.guess_local_raw()
L = dwl.guess_remot_raw()
L = dwl.check_local_files()
L = dwl.invalidate_small_local_files()

dwl.print_table()
dwl.fetch_remote_files()
dwl.print_table()

cnv.load_table_from_prev_step_table(dwl.table)

cnv.print_table()
cnv.convert()

