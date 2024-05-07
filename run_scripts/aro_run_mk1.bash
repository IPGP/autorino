#!/bin/bash 

python3 $HOME/autorino/autorino_run.py -m $HOME/py_ovs/autorino/configfiles/main/autorino_main_cfg_01a.yml -c $HOME/py_ovs/autorino/configfiles/sites/autorino_site_cfg_08a_CFNG.yml 
python3 $HOME/autorino/autorino_run.py -m $HOME/py_ovs/autorino/configfiles/main/autorino_main_cfg_01a.yml -c $HOME/py_ovs/autorino/configfiles/sites/autorino_site_cfg_08a_SNEG.yml
python3 $HOME/autorino/autorino_run.py -m $HOME/py_ovs/autorino/configfiles/main/autorino_main_cfg_01a.yml -c $HOME/py_ovs/autorino/configfiles/sites/autorino_site_cfg_08a_FOAG.yml



