from autorino import cfgfiles as arocfg

###############################################################################
## dummy comment2
pcfg = '/home/sysop/pymods_ovs/autorino/configfiles/proto_config_06d_CFNG.yml'

tup_out = arocfg.read_cfg(pcfg)
workflow_lis, y_site, y_device, y_access = tup_out
arocfg.run_workflow(workflow_lis)

