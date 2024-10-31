#!/bin/bash 


AROHOME="$HOME/py_ovs/autorino"
AROCFG="${AROHOME}_configfiles/configfiles/OVPF/"

CMD1="python3 $AROHOME/autorino/autorino_cfgfile_run.py -m $AROCFG/main/autorino_main_cfg_01a.yml -c $AROCFG/sites/autorino_site_cfg_08a_CFNG.yml"
CMD2="python3 $AROHOME/autorino/autorino_cfgfile_run.py -m $AROCFG/main/autorino_main_cfg_01a.yml -c $AROCFG/sites/autorino_site_cfg_08a_SNEG.yml"
CMD3="python3 $AROHOME/autorino/autorino_cfgfile_run.py -m $AROCFG/main/autorino_main_cfg_01a.yml -c $AROCFG/sites/autorino_site_cfg_08a_FOAG.yml"

echo $CMD1
echo $CMD2
echo $CMD3


$CMD1
$CMD2
$CMD3

