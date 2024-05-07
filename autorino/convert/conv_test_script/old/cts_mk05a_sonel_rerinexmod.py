#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  4 15:43:28 2023

@author: psakicki
"""

#### Import star style
from geodezyx import *                   # Import the GeodeZYX modules
from geodezyx.externlib import *         # Import the external modules
from geodezyx.megalib.megalib import *   # Import the legacy modules names

import rinexmod_api, os
from pathlib import Path

p = "/scratch/convgnss/021_SONEL_conv_GP/rinexmoded"
flist = utils.find_recursive(p,"*crx.gz")
outdir_rinexmoded = "/scratch/convgnss/031_SONEL_conv_redo_GP"

p = "/scratch/convgnss/020_SONEL_conv/rinexmoded"
flist = utils.find_recursive(p,"*crx.gz")
outdir_rinexmoded = "/scratch/convgnss/031_SONEL_conv_redo_PF"

########### SITELOGS
psitelogs = "/work/metadata/SITELOGS"
sitelogs = rinexmod_api.sitelog_input_manage(psitelogs,force=False)


for frnxtmp in flist:
    frnxtmp = Path(frnxtmp)
    ext = frnxtmp.suffix.upper()
    site = frnxtmp.name[:4]
    outdir_rinexmoded_use = os.path.join(outdir_rinexmoded,site)
    
    utils.create_dir(outdir_rinexmoded_use)

    rinexmod_api.rinexmod(str(frnxtmp),
                          outdir_rinexmoded_use,
                          compression=None,
                          longname=True,
                          sitelog=sitelogs,
                          force_rnx_load=True,
                          verbose=True,
                          full_history=True)
