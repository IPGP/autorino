#!/bin/bash 


AROHOME="$HOME/py_ovs/autorino"
AROCFG="$AROHOME/configfiles_ovpf"

python3 $AROHOME/autorino/autorino_run.py -m $AROCFG/main/autorino_main_cfg_01a.yml -c $AROCFG/sites/autorino_site_cfg_08a_CFNG.yml 
python3 $AROHOME/autorino/autorino_run.py -m $AROCFG/main/autorino_main_cfg_01a.yml -c $AROCFG/sites/autorino_site_cfg_08a_SNEG.yml
python3 $AROHOME/autorino/autorino_run.py -m $AROCFG/main/autorino_main_cfg_01a.yml -c $AROCFG/sites/autorino_site_cfg_08a_FOAG.yml



