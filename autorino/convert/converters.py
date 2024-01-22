#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 21 16:23:06 2023

@author: psakic
"""


from typing import Union, List
from pathlib import Path
import os
import re
import subprocess
from subprocess import Popen, PIPE
from geodezyx import utils, operational, conv
import datetime as dt

import autorino.convert as arcv

#### Import the logger
import logging
log = logging.getLogger(__name__)
log.setLevel("DEBUG")

#############################################################################
### Low level functions


def _find_converted_files(directory, pattern_main, pattern_annex):
    """
    Search for the files in a directory recently created (<10sec)
    matching main & annex patterns 
    """
    now = dt.datetime.now()
    delta = dt.timedelta(seconds=10)
    files_main = []
    files_annex = []
    files_main_time = []
    files_annex_time = []
    for file in os.listdir(directory):
        filepath = os.path.join(directory, file)
        if os.path.isfile(filepath):
            created_time = dt.datetime.fromtimestamp(os.path.getctime(filepath))
            if now - created_time < delta and re.match(pattern_main, file):
                files_main.append(filepath)
                files_main_time.append(created_time)
            elif now - created_time < delta and re.match(pattern_annex, file):
                files_annex.append(filepath)
                files_annex_time.append(created_time)
            else:
                pass
            
    #we sort the files found
    files_main = [x for _, x in sorted(zip(files_main_time, files_main))]
    files_annex = [x for _, x in sorted(zip(files_annex_time, files_annex))]
    
    if len(files_main) > 1:
        log.warning("several converted main files found %s", files_main)
        files_main = [files_main[-1]]
        log.warning("keep most recent only: %s",files_main[0])
            
    return files_main, files_annex


## https://stackoverflow.com/questions/36495669/difference-between-terms-option-argument-and-parameter
## https://tinf2.vub.ac.be/~dvermeir/mirrors/www-wks.acs.ohio-state.edu/unix_course/intro-14.html
## https://discourse.ubuntu.com/t/command-structure/18556

def _ashtech_name_2_date(inp_raw_fpath):
    """
    get the record date from an ASHTECH file name
    returns the year, day of year, GPS week, and day of week, and 
    Python datetime
    """
    
    inp_raw_fpath = Path(inp_raw_fpath)
    doy = int(inp_raw_fpath.suffix[1:])
    yy = int(inp_raw_fpath.stem[-2:])
    
    if yy < 80:
        y2k = 2000
    else:
        y2k = 1900
        
    yyyy  = y2k + yy
    
    date = conv.doy2dt(yyyy, doy)
    week,dow = conv.dt2gpstime(date)
    
    return yyyy,doy,week,dow,date

###################################################################
#### conversion function


def _converter_select(converter_inp,inp_raw_fpath=None):

    if converter_inp == "auto" and not inp_raw_fpath:
        log.error("not converter nor input file given, \
                  unable to returns the right conversion fcts")
        raise Exception 
        
    ## for RINEX handeling, inp_raw_fpath can ben an iterable (list)
    ## thus we just keep the 1st elt
    if utils.is_iterable(inp_raw_fpath):
        inp_raw_fpath = inp_raw_fpath[0]
        
    if converter_inp == "auto":
        inp_raw_fpath = Path(inp_raw_fpath)
        ext = inp_raw_fpath.suffix.upper()
        fname = inp_raw_fpath.name.upper()
    else:
        ext = ""
    
    ##### TRIMBLE
    if ext in (".T00",".T02") or converter_inp == "trm2rinex":
        converter_name = "trm2rinex"
        brand = "Trimble"
        cmd_build_fct = arcv.cmd_build_trm2rinex
        conv_regex_fct = arcv.conv_regex_trm2rinex
        bin_options = [] 
        bin_kwoptions = dict() 

    elif ext == ".T02" or converter_inp == "runpkr00":
        converter_name = "runpkr00"
        brand = "Trimble"
        cmd_build_fct = arcv.cmd_build_runpkr00  
        conv_regex_fct = arcv.conv_regex_runpkr00
        bin_options = [] 
        bin_kwoptions = dict() 

    elif ext in (".TGD","TG!") or converter_inp == "teqc":
        converter_name = "teqc"
        brand = "Trimble"
        cmd_build_fct = arcv.cmd_build_teqc
        conv_regex_fct = arcv.conv_regex_teqc
        bin_options = [] 
        bin_kwoptions = dict() 

    ##### ASHTECH 
    elif (re.match(".([0-9]{3})",ext) and fname[0] in ("U","R","B")):
        converter_name = "teqc"
        brand = "Ashtech"
        cmd_build_fct = arcv.cmd_build_teqc
        conv_regex_fct = arcv.conv_regex_teqc
        yyyy,doy,week,dow,date = _ashtech_name_2_date(inp_raw_fpath)
        ftype = fname[0].lower()
        if ftype == "b":
            ftype = "d"
        bin_options = ["-ash " + ftype + " -week " + str(week)] 
        #bin_kwoptions = {"-week": str(week)}
        bin_kwoptions = dict() 

    ##### LEICA 
    elif re.match(".(M[0-9]{2}|MDB)",ext) or converter_inp == "mdb2rinex":
        converter_name = "mdb2rinex"
        brand = "Leica"
        cmd_build_fct = arcv.cmd_build_mdb2rinex    
        conv_regex_fct = arcv.conv_regex_mdb2rnx
        bin_options = [] 
        bin_kwoptions = dict() 
        
    ##### SEPTENTRIO  
    elif re.match(".[0-9]{2}_", ext) or converter_inp == "sbf2rin":
        converter_name = "sbf2rin"
        brand = "Septentrio"
        cmd_build_fct = arcv.cmd_build_sbf2rin
        conv_regex_fct = arcv.conv_regex_void
        bin_options = [] 
        bin_kwoptions = dict() 

    ##### GENERIC BINEX  
    elif ext == ".BNX" or converter_inp == "convbin":
        converter_name = "convbin"
        brand = "Generic BINEX"
        cmd_build_fct = arcv.cmd_build_convbin
        conv_regex_fct = arcv.conv_regex_convbin
        bin_options = [] 
        bin_kwoptions = dict() 

    ##### TOPCON
    elif ext == ".TPS" or converter_inp == "tps2rin":
        converter_name = "tps2rin"
        brand = "Topcon"
        cmd_build_fct = arcv.cmd_build_tps2rin
        conv_regex_fct = arcv.conv_regex_tps2rin
        bin_options = [] 
        bin_kwoptions = dict() 
    else:
        log.error("unable to find the right converter for %s",
                  inp_raw_fpath)
        raise Exception

    return converter_name , brand, cmd_build_fct , conv_regex_fct , bin_options , bin_kwoptions         


def converter_run(inp_raw_fpath: Union[Path,str,List[Path],List[str]],
                  out_dir: Union[Path,str] = None,
                  converter = 'auto',
                  timeout=60,
                  bin_options = [],
                  bin_kwoptions = dict(),
                  bin_path: Union[Path,str] = "",
                  remove_converted_annex_files=False,
                  cmd_build_fct = None,
                  conv_regex_fct = None):
    """
    Generic function to run an external RAW > RINEX conversion program.
    It will detect automatically which converter has to be executed based on 
    input RAW file extension, 
    but this can be customized

    Parameters
    ----------
    inp_raw_fpath : Union[Path,str]
        path of the input RAW file.
        for RINEX Handeling (e.g. splice) a list of path is allowed.
    out_dir : Union[Path,str], optional
        destination directory of the converted RINEX. The default is None.
    converter : str, optional
        name of the converter used.
        Supports : 
            'auto' (automatic choice based on the extension),
            'trm2rnx' (Trimble),
            'runpkr00' (Trimble legacy),
            'teqc' (legacy conversion & RINEX Handeling),
            'mdb2rinex' (Leica),
            'sbf2rin' (Septentrio),
            'convbin' (BINEX),
            'tps2rin' (Topcon),       
            'gfzrnx' (RINEX Handeling)
        see `_converter_select` function and `cmd_build` module 
        for more details.
        The default is 'auto'.
    timeout : int, optional
        timeout in second for the conversion program call.
        The default is 60.
    bin_options : list, optional
        options for the conversion program. The default is [].
    bin_kwoptions : dict, optional
        keyword options for the conversion program. The default is dict().
    bin_path : Union[Path,str], optional
        path of the conversion program bin. The default is "".
    remove_converted_annex_files : bool, optional
        remove or not the 'annex' converted files.
        i.e. the not navigation files (e.g. the navigtation RINEXs).
        The default is False.
    cmd_build_fct : function, optional
        A custom function which build the command calling
        the conversion program
        See `cmd_build` module for more details.
        The default is None.
    conv_regex_fct : function, optional
        A custom function which build the regular expression to find
        the RINEX created during the conversion.
        See `cmd_regex` module for more details.
        The default is None.

    Raises
    ------
    FileNotFoundError

    Returns
    -------
    out_fpath
        the path of the converted RINEX.
    process_converter
        The subprocess object which ran the conversion (for debug purposes).
    """
    
    #### Convert the paths as Path objects
    out_dir = Path(out_dir)
    ## for RINEX handeling, inp_raw_fpath can ben an iterable (list)
    if utils.is_iterable(inp_raw_fpath):
        raw_fpath_multi = [Path(e) for e in inp_raw_fpath]
        raw_fpath_mono = raw_fpath_multi[0]
        raw_fpath = raw_fpath_multi 
    else: # a single  file, most common case
        raw_fpath_multi = [Path(inp_raw_fpath)]
        raw_fpath_mono = Path(inp_raw_fpath)
        raw_fpath = raw_fpath_mono
           

    #### Check if input file exists
    for f in raw_fpath_multi:
        log.info("input file: %s", f)
        if not f.is_file():
            log.error("input file not found: %s", f)
            raise FileNotFoundError
    
    
    # _converter_select can manage both a raw_fpath_mono or raw_fpath_multi
    out_conv_sel = _converter_select(converter,raw_fpath)
    converter_name,brand,cmd_build_fct_use,conv_regex_fct_use,\
        bin_options_use,bin_kwoptions_use = out_conv_sel
    
    #### Force the arcv.cmd_build_fct, if any
    if cmd_build_fct:
        cmd_build_fct_use = cmd_build_fct

    #### Force the arcv.conv_regex_fct, if any        
    if conv_regex_fct:
        conv_regex_fct_use = conv_regex_fct

    #### Force the bin_options if any        
    if bin_options:
        bin_options_use = bin_options
    
    #### Force the bin_kwoptions if any        
    if bin_kwoptions:
        bin_kwoptions_use = bin_kwoptions

    #### build the command
    cmd_use, cmd_list, cmd_str = cmd_build_fct_use(raw_fpath,
                                                   out_dir,
                                                   bin_options_use,
                                                   bin_kwoptions_use)
                                                   ##### BIN PATH !!!!! XXXXX
    log.debug("conversion command: %s", cmd_str)

    ############# run the external conversion programm #############
    timeout_reached = False
    start = dt.datetime.now()
    try:
        process_converter = subprocess.run(cmd_use,
                                           executable="/bin/bash",
                                           shell=True,
                                           stdout=PIPE,
                                           stderr=PIPE,
                                           timeout=timeout)
    except subprocess.TimeoutExpired:
        process_converter = None
        timeout_reached = True
        
    end = dt.datetime.now()
    exec_time = (end - start).seconds + (end - start).microseconds * 10**-6

    #################################################################
   
    ###### check the output  on the conversion programm
    if timeout_reached:
        log.error("Error while converting %s",raw_fpath_mono.name)
        log.error("Timeout reached (%s seconds)",timeout)
    elif process_converter.returncode != 0:
        log.error("Error while converting %s",raw_fpath_mono.name)
        log.error("Converter's error message:")
        log.error(process_converter.stderr)
    else:
        log.debug("Conversion done (%7.4f sec.). Converter's output:", exec_time)
        log.debug(process_converter.stdout)
        
    ###### get the converted file
    #### generate the regex matching the theoretical name for the converted file
    #### if a list of input file is given, the 1st one is used as output name
    conv_regex_main, conv_regex_annex = conv_regex_fct_use(raw_fpath_mono)
    log.debug("regex for the converted files (main/annex.): %s,%s",
              conv_regex_main,
              conv_regex_annex)
    
    #### find the converted file matching the regex 
    conv_files_main, conv_files_annex = _find_converted_files(out_dir,
                                                              conv_regex_main, 
                                                              conv_regex_annex)

    if not conv_files_main:
        out_fpath = ""
        log.error("✗ converted file not found")
    else:
        out_fpath = Path(conv_files_main[0])
        log.info("✓ conversion OK (%7.4f sec.), main file/size: %s %s", 
                 exec_time,
                 out_fpath, 
                 out_fpath.stat().st_size)
        
    if remove_converted_annex_files:
        for f in conv_files_annex:
            os.remove(f)
            log.info("converted annex file removed: %s", f)

    return str(out_fpath), process_converter
