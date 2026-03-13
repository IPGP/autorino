#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 21 16:23:06 2023

@author: psakic
"""

import datetime as dt
import os
import re
import subprocess
from pathlib import Path
from subprocess import PIPE
from typing import Union, List

import autorino.convert as arocnv
from geodezyx import utils, conv

#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger("autorino")
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])

###################################################################
# +++++ conversion function


def _convert_select(converter_inp, inp_raw_fpath=None):
    """
    internal function for ``converter_run``.
    Find the correct RAW > RINEX converter and gives its corresponding attributes

    Returns directly those attributes based on `converter_inp` keyword,
    or can do a basic research based on the RAW file extension

    See also autorino.conv_fcts.slct_conv_odd_f
    for the converter selection of oddly named files

    Parameters
    ----------
    converter_inp : str
        name of the converter used.
        see ``converter_run`` help for more details
    inp_raw_fpath : Path, optional
        RAW file path. used for converter research based on the RAW
        file extension. The default is None.

    Returns
    -------
    converter_name : str
        converter's name.
    brand : str
        converter's name/manufacturer.
    cmd_build_fct : function
        interface function with the converter to perform the conversion.
        see ``converter_run``'s help for more details
    conv_regex_fct : function
        interface function to find the converted file with a regular expression.
    bin_options : list
        options for the conversion program. The default is [].
    bin_kwoptions : dict
        keyword options for the conversion program. The default is dict().
    """

    if converter_inp == "auto" and not inp_raw_fpath:
        logger.error(
            "not converter nor input file given, \
                  unable to returns the right conversion fcts"
        )
        raise Exception

    # + for RINEX handeling, inp_raw_fpath can ben an iterable (list)
    # + thus we just keep the 1st elt
    if utils.is_iterable(inp_raw_fpath):
        inp_raw_fpath = inp_raw_fpath[0]

    if converter_inp == "auto":
        inp_raw_fpath = Path(inp_raw_fpath)
        ext = inp_raw_fpath.suffix.upper()
        fname = inp_raw_fpath.name.upper()
        if ext in (".GZ", ".7Z", ".7ZIP", ".ZIP", ".Z"):
            logger.debug("%s is compressed", fname)
            ext = Path(Path(fname).stem).suffix.upper()
            fname = Path(Path(fname).stem).name.upper()

    else:
        inp_raw_fpath = Path(inp_raw_fpath)
        ext = ""
        fname = inp_raw_fpath.name.upper()

    # +++++ TRIMBLE
    # preliminary tests: Trimble default converter must be extracted from the environment values
    if ext in (".T00", ".T01", ".T02", ".T04") and converter_inp == "auto":
        converter_inp = aroenv.ARO_ENV_DIC["general"]["trimble_default_software"]
        logger.debug(
            "Trimble default converter defined in environnement: %s", converter_inp
        )

    # main test for Trimble : choose the right converter
    if ext in (".T00", ".T01", ".T02", ".T04") and converter_inp == "t0xconvert":
        converter_name = "t0xconvert"
        brand = "Trimble (official converter)"
        cmd_build_fct = arocnv.cmd_build_t0xconvert
        conv_regex_fct = arocnv.conv_regex_t0xconvert
        bin_options = []
        bin_kwoptions = dict()

    elif ext in (".T00", ".T01", ".T02", ".T04") and converter_inp == "trm2rinex":
        converter_name = "trm2rinex"
        brand = "Trimble (unofficial Docker converter)"
        cmd_build_fct = arocnv.cmd_build_trm2rinex
        conv_regex_fct = arocnv.conv_regex_trm2rinex
        bin_options = []
        bin_kwoptions = dict()

    elif ext == (".T00", ".T01", ".T02", ".T04") and converter_inp == "runpkr00":
        converter_name = "runpkr00"
        brand = "Trimble (legacy converter)"
        cmd_build_fct = arocnv.cmd_build_runpkr00
        conv_regex_fct = arocnv.conv_regex_runpkr00
        bin_options = []
        bin_kwoptions = dict()

    elif ext in (".TGD", "TG!") or converter_inp == "teqc":
        converter_name = "teqc"
        brand = "Trimble"
        cmd_build_fct = arocnv.cmd_build_teqc
        conv_regex_fct = arocnv.conv_regex_teqc
        bin_options = []
        bin_kwoptions = dict()

    # +++++ ASHTECH
    elif re.match(".([0-9]{3})", ext) and fname[0] in ("U", "R", "B"):
        converter_name = "teqc"
        brand = "Ashtech"
        cmd_build_fct = arocnv.cmd_build_teqc
        conv_regex_fct = arocnv.conv_regex_teqc
        yyyy, doy, week, dow, date = _ashtech_name_2_date(inp_raw_fpath)
        ftype = fname[0].lower()
        if ftype == "b":
            ftype = "d"
        bin_options = ["-ash " + ftype + " -week " + str(week)]
        # bin_kwoptions = {"-week": str(week)}
        bin_kwoptions = dict()

    # +++++ LEICA
    elif re.match(".(M[0-9]{2}|MDB)", ext) or converter_inp == "mdb2rinex":
        converter_name = "mdb2rinex"
        brand = "Leica"
        cmd_build_fct = arocnv.cmd_build_mdb2rinex
        conv_regex_fct = arocnv.conv_regex_mdb2rnx
        bin_options = []
        bin_kwoptions = dict()

    # +++++ SEPTENTRIO
    elif re.match(".([0-9]{2}_|.*A)", ext) or converter_inp == "sbf2rin":
        converter_name = "sbf2rin"
        brand = "Septentrio"
        cmd_build_fct = arocnv.cmd_build_sbf2rin
        conv_regex_fct = arocnv.conv_regex_void
        bin_options = []
        bin_kwoptions = dict()

    # +++++ GENERIC BINEX
    elif ext == ".BNX" or converter_inp == "convbin":
        converter_name = "convbin"
        brand = "Generic BINEX"
        cmd_build_fct = arocnv.cmd_build_convbin
        conv_regex_fct = arocnv.conv_regex_convbin
        bin_options = []
        bin_kwoptions = dict()

    # +++++ TOPCON
    elif ext == ".TPS" or converter_inp == "tps2rin":
        converter_name = "tps2rin"
        brand = "Topcon"
        cmd_build_fct = arocnv.cmd_build_tps2rin
        conv_regex_fct = arocnv.conv_regex_tps2rin
        bin_options = []
        bin_kwoptions = dict()

    # +++++ GFZRNX
    elif converter_inp == "gfzrnx":
        converter_name = "gfzrnx"
        brand = "RINEX Handeling (GFZ)"
        cmd_build_fct = arocnv.cmd_build_gfzrnx
        conv_regex_fct = arocnv.conv_regex_gfzrnx
        bin_options = []
        bin_kwoptions = dict()

    # +++++ CONVERTO
    elif converter_inp == "converto":
        converter_name = "converto"
        brand = "RINEX Handeling (IGN)"
        cmd_build_fct = arocnv.cmd_build_converto
        conv_regex_fct = arocnv.conv_regex_converto
        bin_options = []
        bin_kwoptions = dict()

    else:
        logger.error("unable to find the right converter for %s", inp_raw_fpath)
        logger.error(
            "input-given converter: %s, maybe not implemented yet?", converter_inp
        )
        raise Exception

    logger.debug("brand & converter selected: %s, %s", brand, converter_name)
    return (
        converter_name,
        brand,
        cmd_build_fct,
        conv_regex_fct,
        bin_options,
        bin_kwoptions,
    )


# set current user as constant
USER, GROUP = arocnv.get_current_user_grp()


def converter_run(
    inp_raw_fpath: Union[Path, str, List[Path], List[str]],
    out_dir: Union[Path, str],
    converter="auto",
    timeout=180,
    bin_options=[],
    bin_kwoptions=dict(),
    bin_path: Union[Path, str] = "",
    remove_converted_annex_files=True,
    cmd_build_fct=None,
    conv_regex_fct=None,
):
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
    out_dir : Union[Path,str]
        destination directory of the converted RINEX.
    converter : str, optional
        name of the converter used.
        Supports :
            * 'auto' (automatic choice based on the extension),
            * 'trm2rnx' (Trimble unofficial),
            * 't0xconvert' (Trimble official),
            * 'runpkr00' (Trimble legacy),
            * 'teqc' (legacy conversion & RINEX Handeling),
            * 'mdb2rinex' (Leica),
            * 'sbf2rin' (Septentrio),
            * 'convbin' (BINEX),
            * 'tps2rin' (Topcon),
            * 'converto' (RINEX Handeling)
            * 'gfzrnx' (RINEX Handeling)
        see ``_convert_select`` function and ``cmd_build`` module
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
        The default is True.
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
    else:  # a single file, most common case
        raw_fpath_multi = [Path(inp_raw_fpath)]
        raw_fpath_mono = Path(inp_raw_fpath)
        raw_fpath = raw_fpath_mono

    #### Check if input file exists
    for f in raw_fpath_multi:
        logger.debug("input file: %s", f)
        if not f.is_file():
            logger.error("input file not found: %s", f)
            raise FileNotFoundError

    if len(raw_fpath_multi) < 2:
        logger.info("input file for conversion: %s", raw_fpath_mono)
    else:
        logger.info("%i input file for conversion", len(raw_fpath_multi))

    # _convert_select can manage both a single file of a list*
    # then could handle both raw_fpath_mono or raw_fpath_multi
    # thus alias variable raw_fpath will work in both cases
    # *. but we thus we just keep the 1st list elt as the representent
    # of the full list (we assue it homogeneous)

    out_conv_sel = _convert_select(converter, raw_fpath)
    (
        converter_name,
        brand,
        cmd_build_fct_use,
        conv_regex_fct_use,
        bin_options_use,
        bin_kwoptions_use,
    ) = out_conv_sel

    #### Force the arocnv.cmd_build_fct, if any
    if cmd_build_fct:
        cmd_build_fct_use = cmd_build_fct

    #### Force the arocnv.conv_regex_fct, if any
    if conv_regex_fct:
        conv_regex_fct_use = conv_regex_fct

    #### Force the bin_options if any
    if bin_options:
        bin_options_use = bin_options

    #### Force the bin_kwoptions if any
    if bin_kwoptions:
        bin_kwoptions_use = bin_kwoptions

    #### build the command
    cmd_use, cmd_list, cmd_str = cmd_build_fct_use(
        raw_fpath, out_dir, bin_options_use, bin_kwoptions_use
    )
    ##### BIN PATH !!!!! XXXXX

    logger.debug("conversion command: %s", cmd_str)

    ############# run the external conversion programm #############
    timeout_reached = False
    start = dt.datetime.now()
    try:
        process_converter = subprocess.run(
            cmd_use,
            executable="/bin/bash",
            shell=True,
            stdout=PIPE,
            stderr=PIPE,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        process_converter = None
        timeout_reached = True

    end = dt.datetime.now()
    exec_time = (end - start).seconds + (end - start).microseconds * 10**-6

    #################################################################

    ###### check the output  on the conversion programm
    if timeout_reached:
        logger.error("Error while converting %s", raw_fpath_mono.name)
        logger.error("Timeout reached (%s seconds)", timeout)
    elif process_converter.returncode != 0:
        logger.error("Error while converting %s", raw_fpath_mono.name)
        logger.error("Converter's error message:")
        logger.error(process_converter.stderr.strip())
    else:
        logger.debug("Conversion done (%7.4f sec.). Converter's output:", exec_time)
        logger.debug(process_converter.stdout.strip())

    ###### get the converted file
    #### generate the regex matching the theoretical name for the converted file
    #### if a list of input file is given, the 1st one is used as output name
    conv_regex_main, conv_regex_annex = conv_regex_fct_use(raw_fpath_mono)
    logger.debug(
        "regex for the converted files (main/annex.): %s,%s",
        conv_regex_main,
        conv_regex_annex,
    )

    #### find the converted file matching the regex
    conv_files_main, conv_files_annex = find_conv_files(
        out_dir, conv_regex_main, conv_regex_annex
    )

    if not conv_files_main:
        out_fpath = ""
        logger.error("✗ converted file not found")
    else:
        out_fpath = Path(conv_files_main[0])
        logger.info(
            "✓ conversion OK (%7.4f sec.), main file/size: %s %s",
            exec_time,
            out_fpath,
            out_fpath.stat().st_size,
        )

    # change ownership
    if out_fpath:
        arocnv.change_owner(out_fpath, USER, GROUP)

    if remove_converted_annex_files:
        for f in conv_files_annex:
            os.remove(f)
            logger.debug("converted annex file removed: %s", f)

    return str(out_fpath), process_converter


#############################################################################
### Low level functions


def find_conv_files(directory, pattern_main, pattern_annex, n_sec=20):
    """
    Searches for the files in a directory that were recently created (within the last n_sec seconds)
    and match the main and annex patterns.

    This function iterates over all files in the specified directory and checks
    if they were created within the last n_sec seconds
    and if their names match the main or annex patterns.
    It returns two lists of files that match the main and annex patterns, respectively.

    Parameters
    ----------
    directory : Path
        The directory in which to search for files.
    pattern_main : str
        The regular expression pattern that the main files should match.
    pattern_annex : str
        The regular expression pattern that the annex files should match.
    n_sec : int, optional
        The number of seconds in the past to consider for file creation.
         Default is 20.

    Returns
    -------
    list
        The list of main files that were found.
    list
        The list of annex files that were found.
    """
    now = dt.datetime.now()
    delta = dt.timedelta(seconds=n_sec)
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

    # Sort the files found
    files_main = [x for _, x in sorted(zip(files_main_time, files_main))]
    files_annex = [x for _, x in sorted(zip(files_annex_time, files_annex))]

    if len(files_main) > 1:
        logger.warning("Several converted main files found %s", files_main)
        files_main = [files_main[-1]]
        logger.warning("Keeping most recent only: %s", files_main[0])

    return files_main, files_annex


## https://stackoverflow.com/questions/36495669/difference-between-terms-option-argument-and-parameter
## https://tinf2.vub.ac.be/~dvermeir/mirrors/www-wks.acs.ohio-state.edu/unix_course/intro-14.html
## https://discourse.ubuntu.com/t/command-structure/18556


def _ashtech_name_2_date(inp_raw_fpath):
    """
    Extracts the record date from an ASHTECH file name.

    This function extracts the year, day of year, GPS week, and day of week from the name of an ASHTECH file.
    It also returns the date as a Python datetime object.

    Parameters
    ----------
    inp_raw_fpath : Path
        The path of the input ASHTECH file.

    Returns
    -------
    int
        The year extracted from the file name.
    int
        The day of the year extracted from the file name.
    int
        The GPS week extracted from the file name.
    int
        The day of the week extracted from the file name.
    datetime
        The date extracted from the file name as a Python datetime object.
    """

    inp_raw_fpath = Path(inp_raw_fpath)
    doy = int(inp_raw_fpath.suffix[1:])
    yy = int(inp_raw_fpath.stem[-2:])

    if yy < 80:
        y2k = 2000
    else:
        y2k = 1900

    yyyy = y2k + yy

    date = conv.doy2dt(yyyy, doy)
    week, dow = conv.dt2gpstime(date)

    return yyyy, doy, week, dow, date
