#!/bin/bash 


AROHOME="${HOME}/tests_pierres/autorino"
AROCFG="${HOME}/tests_pierres/autorino_configfiles/configfiles/OVSG"

python3 $AROHOME/autorino/autorino_cfgfile_run.py -m $AROCFG/main/autorino_main_cfg_ovsg_01a.yml -c $AROCFG/sites/autorino_site_cfg_08a_HOUZ.yml



