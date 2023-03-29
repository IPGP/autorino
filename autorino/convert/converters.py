#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 21 16:23:06 2023

@author: psakic
"""


from typing import Union
from pathlib import Path
import os
import re
import subprocess
from subprocess import Popen, PIPE
from geodezyx import utils, operational
import datetime

from autorino.convert import conv_regex, cmd_build



#### Import the logger
import logging
log = logging.getLogger(__name__)

#############################################################################
### Low level functions


def _find_converted_files(directory, pattern_main, pattern_annex):
    """
    Search for the files in a directory recently created (<30sec)
    matching main & annex patterns 
    """
    now = datetime.datetime.now()
    delta = datetime.timedelta(seconds=30)
    recent_files_main = []
    recent_files_annex = []
    for file in os.listdir(directory):
        filepath = os.path.join(directory, file)
        if os.path.isfile(filepath):
            created_time = datetime.datetime.fromtimestamp(os.path.getctime(filepath))
            if now - created_time < delta and re.match(pattern_main, file):
                recent_files_main.append(filepath)
            elif now - created_time < delta and re.match(pattern_annex, file):
                recent_files_annex.append(filepath)
            else:
                pass
            
    if len(recent_files_main) > 1:
        log.warning("several converted main files found %s", recent_files_main)
            
    return recent_files_main, recent_files_annex


## https://stackoverflow.com/questions/36495669/difference-between-terms-option-argument-and-parameter
## https://tinf2.vub.ac.be/~dvermeir/mirrors/www-wks.acs.ohio-state.edu/unix_course/intro-14.html
## https://discourse.ubuntu.com/t/command-structure/18556



###################################################################
#### conversion function


def _converter_select(converter_inp,inp_raw_fpath=None):
    if converter_inp == "auto" and not inp_raw_fpath:
        raise Exception 
        
    if converter_inp == "auto":
        inp_raw_fpath = Path(inp_raw_fpath)
        ext = inp_raw_fpath.suffix.upper()
    else:
        ext = ""
    
    if ext in (".T00",".T02") or converter_inp == "trm2rinex":
        converter_name = "trm2rinex"
        brand = "Trimble"
        cmd_build_fct = cmd_build.cmd_build_trm2rinex
        conv_regex_fct = conv_regex.conv_regex_trm2rinex

    elif ext == ".T02" or converter_inp == "runpkr00":
        converter_name = "runpkr00"
        brand = "Trimble"
        cmd_build_fct = cmd_build.cmd_build_runpkr00  
        conv_regex_fct = conv_regex.conv_regex_runpkr00

    elif ext == ".TGD" or converter_inp == "teqc":
        converter_name = "teqc"
        brand = "Trimble"
        cmd_build_fct = cmd_build.cmd_build_teqc
        conv_regex_fct = conv_regex.conv_regex_teqc

    elif ext in (".MDB",".M00") or converter_inp == "mdb2rinex":
        converter_name = "mdb2rinex"
        brand = "Leica"
        cmd_build_fct = cmd_build.cmd_build_mdb2rinex    
        conv_regex_fct = conv_regex.conv_regex_void
        
    elif re.match("[0-9]{2}_", ext) or converter_inp == "sbf2rin":
        converter_name = "sbf2rin"
        brand = "Septentrio"
        cmd_build_fct = cmd_build.cmd_build_sbf2rin
        conv_regex_fct = conv_regex.conv_regex_void

    elif ext == ".BNX" or converter_inp == "convbin":
        converter_name = "convbin"
        brand = "Generic BINEX"
        cmd_build_fct = cmd_build.cmd_build_convbin
        conv_regex_fct = conv_regex.conv_regex_convbin

    elif ext == ".TPS" or converter_inp == "tps2rin":
        converter_name = "tps2rin"
        brand = "Topcon"
        cmd_build.cmd_build_fct = cmd_build.cmd_build_tps2rin
        conv_regex.conv_regex_fct = conv_regex.conv_regex_tps2rin
    else:
        log.error("unable to find the right converter for %s",
                  inp_raw_fpath)

    print("AAAAAAAAA",ext,converter_inp)
        
    return converter_name , brand, cmd_build_fct , conv_regex_fct
        

def converter_run(inp_raw_fpath: Union[Path,str],
                  out_dir: Union[Path,str] = None,
                  converter = 'auto',
                  bin_options = [],
                  bin_kwoptions = dict(),
                  bin_path: Union[Path,str] = "",
                  remove_converted_annex_files=False,
                  cmd_build_fct = None,
                  conv_regex_fct = None):
    
    #### Convert the paths as Path objects
    inp_raw_fpath = Path(inp_raw_fpath)
    out_dir = Path(out_dir)

    log.info("input file: %s", inp_raw_fpath)

    #### Check if input file exists
    if not inp_raw_fpath.is_file():
        log.error("input file not found: %s", inp_raw_fpath)
        raise FileNotFoundError
         
    out_conv_sel = _converter_select(converter,inp_raw_fpath)
    converter_name,brand,cmd_build_fct_use,conv_regex_fct_use = out_conv_sel
    
    #### Force the cmd_build.cmd_build_fct, if any
    if cmd_build_fct:
        cmd_build_fct_use = cmd_build_fct

    #### Force the conv_regex.conv_regex_fct, if any        
    if conv_regex_fct:
        conv_regex_fct_use = conv_regex_fct    
    
    
    #### build the command
    cmd_use, cmd_list, cmd_str = cmd_build_fct_use(inp_raw_fpath,
                                                   out_dir,
                                                   bin_options,
                                                   bin_kwoptions)
                                                   ##### BIN PATH !!!!! XXXXX
    log.debug("conversion command: %s", cmd_str)

    ############# run the programm #############
    process_converter = subprocess.run(cmd_use,
                                       executable="/bin/bash",
                                       shell=True,
                                       stdout=PIPE,
                                       stderr=PIPE)
    ############################################
    
    ##### ADD a warn if return code !!= 0 XXXXXXXXXXxx
    
    #### Theoretical name for the converted file
    conv_regex_main, conv_regex_annex = conv_regex_fct_use(inp_raw_fpath)
    log.debug("regex for the converted files (main/annex): %s,%s", conv_regex_main, conv_regex_annex)
    
    
    #out_fpath = out_dir.joinpath(out_fname)
    conv_files_main, conv_files_annex = _find_converted_files(out_dir,
                                                              conv_regex_main, 
                                                              conv_regex_annex)

    if not conv_files_main:
        out_fpath = ""
        log.error("✘ converted file not found")
    
    else:
        out_fpath = Path(conv_files_main[0])
        log.info("✔️ conversion OK, main file/size: %s %s", 
                 out_fpath, 
                 out_fpath.stat().st_size)
        
    if remove_converted_annex_files:
        for f in conv_files_annex:
            os.remove(f)
            log.info("converted annex file removed: %s", f)


    return str(out_fpath), process_converter
