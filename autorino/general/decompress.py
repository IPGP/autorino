#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 29 11:53:09 2024

@author: psakicki
"""

from geodezyx import conv
from pathlib import Path
import gzip
import shutil
import hatanaka

#### Import the logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")


 #  _____                                               _             
 # |  __ \                                             (_)            
 # | |  | | ___  ___ ___  _ __ ___  _ __  _ __ ___  ___ _  ___  _ __  
 # | |  | |/ _ \/ __/ _ \| '_ ` _ \| '_ \| '__/ _ \/ __| |/ _ \| '_ \ 
 # | |__| |  __/ (_| (_) | | | | | | |_) | | |  __/\__ \ | (_) | | | |
 # |_____/ \___|\___\___/|_| |_| |_| .__/|_|  \___||___/_|\___/|_| |_|
 #                                 | |                                
 #                                 |_|    


def is_compressed(file_inp):
    file_inp2 = Path(file_inp)
    
    ext = file_inp2.suffix.lower()
    
    if ext in ('.gz',):
        bool_compress = True
    else:
        bool_compress = False
        
    return bool_compress
        
    
def _decomp_gzip(gzip_file_inp, out_dir_inp = None):
    gzip_file_inp = str(gzip_file_inp)
    gzip_file2 = Path(gzip_file_inp)

    if not out_dir_inp:
        out_dir = gzip_file2.parent
    else:
        out_dir = Path(out_dir_inp)

    file_out = out_dir.joinpath(gzip_file2.stem)

    with gzip.open(gzip_file_inp, 'rb') as f_in:
        with open(file_out, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
            
    logger.debug("decompress (gzip): %s > %s", gzip_file2.name, file_out)

    return str(file_out)


def _decomp_hatanaka(crx_file_inp,out_dir_inp = None):
    
    crx_file_inp = str(crx_file_inp)
    crx_file_inp2 = Path(crx_file_inp)
    
    if out_dir_inp:
        crx_file = shutil.copy2(crx_file_inp, out_dir_inp)
        dell = True
    else:
        crx_file = crx_file_inp
        dell = False
    
    rnx_file_out = hatanaka.decompress_on_disk(crx_file,delete=dell)
    logger.debug("decompress (hatanaka): %s > %s", crx_file_inp2.name,
                 rnx_file_out)
    
    return str(rnx_file_out)
    

def decompress(file_inp,
               out_dir_inp = None):

    file_inp = str(file_inp) 
    file_inp2 = Path(file_inp)
    ext = file_inp2.suffix.lower()
    
    ### RINEX Case
    if conv.rinex_regex_search_tester(file_inp,compressed=True):
        file_out = _decomp_hatanaka(file_inp,out_dir_inp)
    ### Generic gzipped case (e.g. RAW file)
    elif ext == ".gz":
        file_out = _decomp_gzip(file_inp,out_dir_inp)
    else:
        logger.info("no valid compression for %s, nothing is done", 
                    file_inp2.name)
        file_out = file_inp
        
    return file_out
