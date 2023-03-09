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


#### Import the logger
import logging
log = logging.getLogger(__name__)

#############################################################################
### Low level functions


def _find_converted_files(directory, pattern_main, pattern_annex):
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


def _kw_options_dict2str(kw_options):
    cmd_list = []
    
    if utils.is_iterable(kw_options):
        pass
    else:
        kw_options = [kw_options]
    
    for kwo in kw_options:
        for key,val in kwo.items():
            cmd_list = cmd_list + [str(key),str(val)]
        
    cmd_str = " ".join(cmd_list)
    
    return cmd_list, cmd_str


def _options_list2str(options):
    cmd_list = []
    for opt in options:
        if type(opt) is str:
            cmd_list.append(opt)
        else:
            cmd_list = cmd_list + opt
        
    cmd_str = " ".join(cmd_list)
    
    return cmd_list, cmd_str


###################################################################
#### command builder functions


def cmd_build_generic(program="",
                      options=[""],
                      kw_options=dict(),
                      arguments="",
                      options_bis=[""],
                      kw_options_bis=dict()): 
    cmd = []

    if utils.is_iterable(program):
        cmd = [str(e) for e in program]
    else:
        cmd = [str(program)]    
        
    for key,val in kw_options.items():
        cmd = cmd + [str(key),str(val)]

    for key,val in kw_options_bis.items():
        cmd = cmd + [str(key),str(val)]
        
    if utils.is_iterable(arguments):
        arguments = [str(e) for e in arguments]
    else:
        arguments = [str(arguments)]
        
    cmd = cmd + options + options_bis + arguments
    
    cmd_str = " ".join(cmd)
    
    return cmd, cmd_str

def cmd_build_trm2rinex(inp_raw_fpath,
                        out_dir,
                        bin_options_custom=[],
                        bin_kwoptions_custom=dict(),
                        bin_path="trm2rinex:cli-light"):

    # docker run --rm -v ${f_dir}:/inp -v ${DIR_out}:/out trm2rinex:cli-light inp/${f_base} -p out/${subdir_out_010} -n -d -s -v 3.04
    
    
    #       data/MAGC320b.2021.rt27 defines the input file (relative to container filesystem root)
    #       -p data/out defines the path for the conversion output (relative to container filesystem root)
    #       -n to NOT perform height reference point corrections
    #       -d to include doppler observables in the output observation file
    #       -co to include clock corrections in the output observation file
    #       -s to include signal strength values in the output observation file
    #       -v 3.04 to choose which RINEX version is generated (cf. command line usage for details)
    #       -h 0.1387 to include the marker to antenna ARP vertical offset into RINEX header

    #### Convert the paths as Path objects
    inp_raw_fpath = Path(inp_raw_fpath)
    out_dir = Path(out_dir)

    cmd_docker_list = ['docker','run','--rm','-v', str(inp_raw_fpath.parent) + ':/inp','-v', str(out_dir) + ':/out']
    cmd_trm2rinex_list = [bin_path, 'inp/' + inp_raw_fpath.name,'-n','-d','-s','-v','3.04','-p', 'out/']

    cmd_opt_list , _ = _options_list2str(bin_options_custom)
    cmd_kwopt_list , _ = _kw_options_dict2str(bin_kwoptions_custom)
    
    cmd_list = cmd_docker_list + cmd_trm2rinex_list + cmd_opt_list + cmd_kwopt_list
    cmd_list = [str(e) for e in cmd_list]
    cmd_str  = " ".join(cmd_list)
    cmd_use = [cmd_str]
    
    return cmd_use, cmd_list, cmd_str

def cmd_build_mdb2rinex(inp_raw_fpath,
                        out_dir,
                        bin_options_custom=[],
                        bin_kwoptions_custom=dict(),
                        bin_path="mdb2rinex"):
  #   Options:
  # -h [ --help ]         Print help messages
  # -v [ --version ]      Print program version
  # -s [ --summary ]      Print tracking summary at end of obs file
  # -o [ --out ] arg      Output directory
  # -f [ --files ] arg    Mdb input file list
    
    #### Convert the paths as Path objects
    inp_raw_fpath = Path(inp_raw_fpath)
    out_dir = Path(out_dir)

    cmd_opt_list , _ = _options_list2str(bin_options_custom)
    cmd_kwopt_list , _ = _kw_options_dict2str(bin_kwoptions_custom)
   
    cmd_list = [bin_path,'--out', out_dir,'--files', inp_raw_fpath] + cmd_opt_list + cmd_kwopt_list
    cmd_list = [str(e) for e in cmd_list]
    cmd_str = " ".join(cmd_list)
    cmd_use = [cmd_str]
    
    return cmd_use, cmd_list, cmd_str

def cmd_build_sbf2rin(inp_raw_fpath,
                      out_dir,
                      bin_options_custom=[],
                      bin_kwoptions_custom=dict(),
                      bin_path="sbf2rin"):
    
  #   sbf2rin -f input_file [-o output_file][-l][-O CCC][-R3][-R210][-n type]
  #                     [-MET][-i interval][-b startepoch][-e endepoch]
  #                     [-s][-D][-X][-c][-C commentstr][-x systems]
  #                     [-I siglist][-E siglist][-a antenna][-ma][-mf]
  #                     [-noevent][-S][-v][-V]

  # -f input_file   (mandatory) Name of the SBF file(s) to be converted.
  #                 To convert multiple files, use a whitespace as
  #                 delimiter between the different file names. Each SBF
  #                 file is converted into a different RINEX file.
  # -o output_file  Name of the output RINEX file, bypassing the standard
  #                 naming convention. See file naming convention below.
  #                 Note: do not use a forced output file name when
  #                 converting multiple files.
  # -l              Use long file naming convention (introduced in RINEX
  #                 v3.02). Default is short file name. See below.
  # -O CCC          Force using the specified 3-letter country code in
  #                 the long file name. This option is ignored if the -l
  #                 option is not used.
  # -R version      By default, sbf2rin converts to RINEX v3.04.
  #                 -R211 converts to v2.11,
  #                 -R303 converts to v3.03,
  #                 -R304 converts to v3.04,
  #                 -R305 converts to v3.05,
  #                 -R400 converts to v4.00,
  #                 -R3 is an alias for -R304,
  #                 -R4 is an alias for -R400.
  # -n type         Type of files to be generated.  type is a combination
  #                 of the following characters:
  #                   O for an observation file (this is the default),
  #                   N for a GPS-only navigation file,
  #                   G for a GLONASS-only navigation file,
  #                   E for a Galileo-only navigation file (always RINEX
  #                     v3.xx or above),
  #                   H for a SBAS-only navigation file,
  #                   I for a BeiDou-only navigation file (always RINEX
  #                     v3.xx or above),
  #                   P for a mixed GNSS navigation file (always RINEX
  #                     v3.xx or above),
  #                   B for a broadcast SBAS file (all L1 and L5 messages),
  #                     valid only for a broadcast SBAS file (valid CRC
  #                     only),
  #                   M for a meteo file.
  #                 Note that QZSS and IRNSS/NavIC navigation data is only
  #                 available in mixed files.
  #                 If multiple characters are combined, all the requested
  #                 RINEX files are generated at once. For example -nPOM
  #                 generates obs, mixed nav and meteo files.
  # -MET            Generate a RINEX meteo file (same as -nM).
  # -i interval     Interval in the RINEX obs and meteo file, in seconds
  #                 (by default, the interval is the same as in the SBF
  #                  file).
  # -b startepoch   Time of first epoch to insert in the RINEX file.
  #                 Format: yyyy-mm-dd_hh:mm:ss or hh:mm:ss.
  # -e endepoch     Last epoch to insert in the RINEX file
  #                 Format: yyyy-mm-dd_hh:mm:ss or hh:mm:ss.
  # -s              Include the Sx obs types in the observation file.
  # -D              Include the Dx obs types in the observation file.
  # -X              Include the X1 obs types (channel number) in the
  #                 observation file.
  #                 (option not available when generating RINEX v2.11
  #                  files).
  # -c              Allow comments in the RINEX file (from the Comment SBF
  #                 block)
  # -C commentstr   Add the specified comment string to the RINEX obs
  #                 header. The comment string must not be longer than
  #                 240 characters. Enclose the string between quotes if
  #                 it contains whitespaces.
  # -U              Make sure a satellite number does not appear more than
  #                 once in a given epoch, which could otherwise happen when
  #                 the receiver is configured to track the same satellite on
  #                 multiple channels, or in rare cases when two GLONASS
  #                 satellites are using the same slot number.
  # -x systems      Exclude one or more satellite systems from the obs
  #                 file or from the mixed navigation file.
  #                 systems may be G (GPS), R (Glonass), E (Galileo), S
  #                 (SBAS), C (Compass/Beidou), J (QZSS), I (IRNSS/NavIC) or
  #                 any combination thereof. For instance, -xERSCJI produces
  #                 a GPS-only file.
  # -I siglist      Include only the observables from the specified signal
  #                 types. By default all observables in the SBF file are
  #                 converted to RINEX. siglist is a list of signal types
  #                 separated by "+" and without whitespaces.  The
  #                 available signal types are:
  #                 GPSL1CA, GPSL1P, GPSL2P, GPSL2C, GPSL5, GPSL1C,
  #                 GLOL1CA, GLOL1P, GLOL2P, GLOL2CA, GLOL3,
  #                 GALE1, GALE5a, GALE5b, GALE5, GALE6,
  #                 BDSB1I, BDSB2I, BDSB3I, BDSB1C, BDSB2a, BDSB2b,
  #                 QZSL1CA, QZSL2C, QZSL5, QZSL1C, QZSL1S, QZSL5S
  #                 SBSL1, SBSL5,
  #                 IRNL5, IRNS1.
  #                 For example: -I GPSL1CA+GLOL1CA
  # -E siglist      Exclude the observables from the specified signal
  #                 types. See the -I argument for a definition of siglist.
  # -a antenna      Convert data from the specified antenna (antenna is 1,
  #                 2 or 3). The default is 1, corresponding to the main
  #                 antenna.
  # -ma             Insert a "start moving" event right after the header
  #                 if the RINEX file contains kinematic data.
  # -mf             Force inserting a "start moving" event right after
  #                 the header.
  # -noevent        Do not report external events in RINEX.  Default is to
  #                 report external events in comment strings.
  # -S              Automatically increase the file sequence character in
  #                 the output file name when converting multiple files
  #                 from the same marker and the same day. This option is
  #                 ignored if the -l or the -o option is also selected.
  # -v              Run in verbose mode.
  # -V              Display the sbf2rin version.
    
    #### Convert the paths as Path objects
    inp_raw_fpath = Path(inp_raw_fpath)
    out_dir = Path(out_dir)
    
    cmd_opt_list , _ = _options_list2str(bin_options_custom)
    cmd_kwopt_list , _ = _kw_options_dict2str(bin_kwoptions_custom)
   
    out_fpath = out_dir.joinpath(inp_raw_fpath.name + ".rnx_sbf2rin")
   
    cmd_list = [bin_path,'-f', inp_raw_fpath, '-o', out_fpath ] + cmd_opt_list + cmd_kwopt_list
    cmd_list = [str(e) for e in cmd_list]
    cmd_str = " ".join(cmd_list)
    cmd_use = [cmd_str]
    
    return cmd_use, cmd_list, cmd_str


def cmd_build_runpkr00(inp_raw_fpath,
                       out_dir,
                       bin_options_custom=[],
                       bin_kwoptions_custom=dict(),
                       bin_path="runpkr00"):

    # runpkr00 - Utility to unpack Trimble R00\T00\T01\T02 files, Version 6.03 (Linux) ( t01lib 8.111 )
    # Copyright (c) Trimble Navigation Limited 1992-2015.  All rights reserved.
    
    # usage: runpkr00 [-deimacfvq] [-sfile] [-x[ehi*]] [-tfmt] [-n[!]] [-u0|1] src[+s2+s3+..+sn] [@file] [out]
    #  @file      file with list of files to be concatenated (one per line)
    #  -c         ignore checksum errors
    #  -a         produce APP file (when possible)
    #  -d         produce DAT file
    #  -e         produce EPH file
    #  -i         produce ION file
    #  -m         produce MES file
    #  -n[!]      fix NetRS serial number, [!-unconditional]
    #  -s[file]   produce Summary file
    #  -f         attempt fixup if possible
    #  -u[0|1]    update file name [0-dft, 1-station]
    #  -v         verbose
    #  -x[ehi*]   exclude initial: e-eph, h-header, i-ionutc, *-all
    #  -tfmt      format type of file (fmt=r00,t00,t01,t02)
    #  -q         quick summary to std out
    #  -g         use type 27 (if it exists) and allow extended type 17
    
    # examples: runpkr00 -d gs00233a
    #           runpkr00 -dev gs00233a gnew233a
    #           runpkr00 -deimv gs00233a c:\new\gs00233a
    #           runpkr00 -de c:\old\gs00233a c:\new\gs00233a
    #           runpkr00 -demv gs00233a+gs00233b+gs00233c comb2330
    #           runpkr00 -demv @r00.lst comb2330

    #### Convert the paths as Path objects
    inp_raw_fpath = Path(inp_raw_fpath)
    out_dir = Path(out_dir)
    
    cmd_opt_list , _ = _options_list2str(bin_options_custom)
    cmd_kwopt_list , _ = _kw_options_dict2str(bin_kwoptions_custom)
   
    cmd_list = [bin_path,"-g","-d"] + cmd_opt_list + cmd_kwopt_list + [inp_raw_fpath,out_dir]
    cmd_list = [str(e) for e in cmd_list]
    cmd_str = " ".join(cmd_list)
    cmd_use = [cmd_str]
    
    return cmd_use, cmd_list, cmd_str


def cmd_build_teqc(inp_raw_fpath,
                   out_dir,
                   bin_options_custom=[],
                   bin_kwoptions_custom=dict(),
                   bin_path="teqc"):
    
    
    #### Convert the paths as Path objects
    inp_raw_fpath = Path(inp_raw_fpath)
    out_dir = Path(out_dir)

    out_fpath = out_dir.joinpath(inp_raw_fpath.with_suffix(".rnx_teqc"))   
    
    cmd_opt_list , _ = _options_list2str(bin_options_custom)
    cmd_kwopt_list , _ = _kw_options_dict2str(bin_kwoptions_custom)
    
    cmd_list = [bin_path,'+out',out_fpath] + cmd_opt_list + cmd_kwopt_list + [inp_raw_fpath]
    cmd_list = [str(e) for e in cmd_list]
    cmd_str = " ".join(cmd_list)
    cmd_use = [cmd_str]
    
    return cmd_use, cmd_list, cmd_str
    
def cmd_build_convbin(inp_raw_fpath,
                   out_dir,
                   bin_options_custom=[],
                   bin_kwoptions_custom=dict(),
                   bin_path="/home/psakicki/SOFTWARE/RTKLIB_explorer/RTKLIB/app/consapp/convbin/gcc/convbin"):
    
    # Synopsys

    # convbin [option ...] file
    
    # Description
    
    # Convert RTCM, receiver raw data log and RINEX file to RINEX and SBAS/LEX
    # message file. SBAS message file complies with RTKLIB SBAS/LEX message
    # format. It supports the following messages or files.
    
    # RTCM 2                : Type 1, 3, 9, 14, 16, 17, 18, 19, 22
    # RTCM 3                : Type 1002, 1004, 1005, 1006, 1010, 1012, 1019, 1020
    #                         Type 1071-1127 (MSM except for compact msg)
    # NovAtel OEMV/4,OEMStar: RANGECMPB, RANGEB, RAWEPHEMB, IONUTCB, RAWWASSFRAMEB
    # u-blox LEA-4T/5T/6T/8/9  : RXM-RAW, RXM-RAWX, RXM-SFRB
    # Swift Piksi Multi     : 
    # Hemisphere            : BIN76, BIN80, BIN94, BIN95, BIN96
    # SkyTraq S1315F        : msg0xDD, msg0xE0, msg0xDC
    # GW10                  : msg0x08, msg0x03, msg0x27, msg0x20
    # Javad                 : [R*],[r*],[*R],[*r],[P*],[p*],[*P],[*p],[D*],[*d],
    #                         [E*],[*E],[F*],[TC],[GE],[NE],[EN],[QE],[UO],[IO],
    #                         [WD]
    # NVS                   : BINR
    # BINEX                 : big-endian, regular CRC, forward record (0xE2)
    #                         0x01-01,0x01-02,0x01-03,0x01-04,0x01-06,0x7f-05
    # Trimble               : RT17
    # Septentrio            : SBF
    # RINEX                 : OBS, NAV, GNAV, HNAV, LNAV, QNAV
    
    # Options [default]
    
    #     file         input receiver binary log file
    #     -ts y/m/d h:m:s  start time [all]
    #     -te y/m/d h:m:s  end time [all]
    #     -tr y/m/d h:m:s  approximated time for RTCM
    #     -ti tint     observation data interval (s) [all]
    #     -tt ttol     observation data epoch tolerance (s) [0.005]
    #     -span span   time span (h) [all]
    #     -r format    log format type
    #                  rtcm2= RTCM 2
    #                  rtcm3= RTCM 3
    #                  nov  = NovAtel OEM/4/V/6/7,OEMStar
    #                  ubx  = ublox LEA-4T/5T/6T/7T/M8T/F9
    #                  sbp  = Swift Navigation SBP
    #                  hemis= Hemisphere Eclipse/Crescent
    #                  stq  = SkyTraq S1315F
    #                  javad= Javad GREIS
    #                  nvs  = NVS NV08C BINR
    #                  binex= BINEX
    #                  rt17 = Trimble RT17
    #                  sbf  = Septentrio SBF
    #                  rinex= RINEX
    #     -ro opt      receiver options
    #     -f freq      number of frequencies [5]
    #     -hc comment  rinex header: comment line
    #     -hm marker   rinex header: marker name
    #     -hn markno   rinex header: marker number
    #     -ht marktype rinex header: marker type
    #     -ho observ   rinex header: oberver name and agency separated by /
    #     -hr rec      rinex header: receiver number, type and version separated by /
    #     -ha ant      rinex header: antenna number and type separated by /
    #     -hp pos      rinex header: approx position x/y/z separated by /
    #     -hd delta    rinex header: antenna delta h/e/n separated by /
    #     -v ver       rinex version [3.04]
    #     -od          include doppler frequency in rinex obs [on]
    #     -os          include snr in rinex obs [on]
    #     -oi          include iono correction in rinex nav header [off]
    #     -ot          include time correction in rinex nav header [off]
    #     -ol          include leap seconds in rinex nav header [off]
    #     -halfc       half-cycle ambiguity correction [off]
    #     -mask   [sig[,...]] signal mask(s) (sig={G|R|E|J|S|C|I}L{1C|1P|1W|...})
    #     -nomask [sig[,...]] signal no mask (same as above)
    #     -x sat       exclude satellite
    #     -y sys       exclude systems (G:GPS,R:GLO,E:GAL,J:QZS,S:SBS,C:BDS,I:IRN)
    #     -d dir       output directory [same as input file]
    #     -c staid     use RINEX file name convention with staid [off]
    #     -o ofile     output RINEX OBS file
    #     -n nfile     output RINEX NAV file
    #     -g gfile     output RINEX GNAV file
    #     -h hfile     output RINEX HNAV file
    #     -q qfile     output RINEX QNAV file
    #     -l lfile     output RINEX LNAV file
    #     -b cfile     output RINEX CNAV file
    #     -i ifile     output RINEX INAV file
    #     -s sfile     output SBAS message file
    #     -trace level output trace level [off]
    
    # If any output file specified, default output files (<file>.obs,
    # <file>.nav, <file>.gnav, <file>.hnav, <file>.qnav, <file>.lnav,
    # <file>.cnav, <file>.inav and <file>.sbs) are used. To obtain week number info
    # for RTCM file, use -tr option to specify the approximated log start time.
    # Without -tr option, the program obtains the week number from the time-tag file (if it exists) or the last modified time of the log file instead.
    
    # If receiver type is not specified, type is recognized by the input
    # file extension as follows.
    #     *.rtcm2       RTCM 2
    #     *.rtcm3       RTCM 3
    #     *.gps         NovAtel OEM4/V/6/7,OEMStar
    #     *.ubx         u-blox LEA-4T/5T/6T/7T/M8T/F9
    #     *.sbp         Swift Navigation SBP
    #     *.bin         Hemisphere Eclipse/Crescent
    #     *.stq         SkyTraq S1315F
    #     *.jps         Javad GREIS
    #     *.bnx,*binex  BINEX
    #     *.rt17        Trimble RT17
    #     *.sbf         Septentrio SBF
    #     *.obs,*.*o    RINEX OBS
    #     *.rnx         RINEX OBS     *.nav,*.*n    RINEX NAV
    
    #### Convert the paths as Path objects
    inp_raw_fpath = Path(inp_raw_fpath)
    out_dir = Path(out_dir)
    
    cmd_opt_list , _ = _options_list2str(bin_options_custom)
    cmd_kwopt_list , _ = _kw_options_dict2str(bin_kwoptions_custom)
    
    cmd_list = [bin_path,'-d',out_dir,'-r','binex'] + cmd_opt_list + cmd_kwopt_list + [inp_raw_fpath]
    cmd_list = [str(e) for e in cmd_list]
    cmd_str = " ".join(cmd_list)
    cmd_use = [cmd_str]
    
    return cmd_use, cmd_list, cmd_str
    



###################################################################
#### converted files regular expressions functions
#### main = the regex for the main file i.e. the Observation RINEX
#### annex = the regex for the ALL outputed files (Observation RINEX included)
#### the main with be processed before the annex, 
#### thus annex regex will finally not include the main
    
def conv_regex_void(f):
    f = Path(Path(f).name) ### keep the filename only
    conv_regex_main = re.compile(f.name)
    conv_regex_annex = re.compile(f.name)
    return conv_regex_main , conv_regex_annex

def conv_regex_runpkr00(f): 
    # PSA1______202110270000A.tgd
    # PSA1______202110270000A.tg! (opened/working file)
    # ABD0______202110270000A.dat
    f = Path(Path(f).name) ### keep the filename only
    conv_regex_main = re.compile(f.with_suffix(".tgd").name)
    conv_regex_annex  = re.compile(f.stem)
    return conv_regex_main , conv_regex_annex

def conv_regex_teqc(f): 
    f = Path(Path(f).name) ### keep the filename only
    conv_regex_main = re.compile(f.with_suffix(".rnx_teqc").name)
    conv_regex_annex  = conv_regex_main
    return conv_regex_main , conv_regex_annex

def conv_regex_trm2rinex(f):
    # "/home/psakicki/aaa_FOURBI/convertertest/AGAL______202110270000A.21o",
    # "/home/psakicki/aaa_FOURBI/convertertest/AGAL______202110270000A.21l",
    # "/home/psakicki/aaa_FOURBI/convertertest/AGAL______202110270000A.21g",
    # "/home/psakicki/aaa_FOURBI/convertertest/AGAL______202110270000A.21n"
    f = Path(Path(f).name) ### keep the filename only
    yyyy = re.search("[0-9]{4}",f.name).group()
    conv_regex_main = re.compile(f.with_suffix("." + yyyy[2:] + "o").name)
    conv_regex_annex = re.compile(f.with_suffix("." + yyyy[2:]).name)
    return conv_regex_main , conv_regex_annex

def conv_regex_mdb2rnx(f):
    # souf3000.21o
    # souf3000.21n
    # souf3000.21l
    # souf3000.21g
    f = Path(Path(f).name) ### keep the filename only    
    regex_doy_site=r"(\w{4})([0-9]{3})"
    site=re.match(regex_doy_site,f.name).group(1).lower()
    doy=re.match(regex_doy_site,f.name).group(2).lower()
    conv_regex_main = re.compile(site+doy+".\.[0-9]{2}o")
    conv_regex_annex  = re.compile(site+doy+".\.[0-9]{2}\w")
    return conv_regex_main , conv_regex_annex
    
def conv_regex_convbin(f):
    # Input
    # NBIM0a20221226.BNX
    # Output
    #NBIM0a20221226.obs
    #NBIM0a20221226.nav
    #NBIM0a20221226.sbs
    conv_regex_main = re.compile(f.with_suffix(".obs").name)
    conv_regex_annex  = re.compile(f.stem)
    return conv_regex_main , conv_regex_annex



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
        cmd_build_fct = cmd_build_trm2rinex
        conv_regex_fct = conv_regex_trm2rinex

    elif ext == ".T02" or converter_inp == "runpkr00":
        converter_name = "runpkr00"
        brand = "Trimble"
        cmd_build_fct = cmd_build_runpkr00  
        conv_regex_fct = conv_regex_runpkr00

    elif ext == ".TGD" or converter_inp == "teqc":
        converter_name = "teqc"
        brand = "Trimble"
        cmd_build_fct = cmd_build_teqc
        conv_regex_fct = conv_regex_teqc

    elif ext in (".MDB",".M00") or converter_inp == "mdb2rinex":
        converter_name = "mdb2rinex"
        brand = "Leica"
        cmd_build_fct = cmd_build_mdb2rinex    
        conv_regex_fct = conv_regex_void
        
    elif re.match("[0-9]{2}_", ext) or converter_inp == "sbf2rin":
        converter_name = "sbf2rin"
        brand = "Septentrio"
        cmd_build_fct = cmd_build_sbf2rin
        conv_regex_fct = conv_regex_void

    elif ext == ".BNX" or converter_inp == "convbin":
        converter_name = "convbin"
        brand = "BINEX"
        cmd_build_fct = cmd_build_convbin
        conv_regex_fct = conv_regex_convbin
        
    return converter_name , cmd_build_fct , conv_regex_fct
        

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
    converter_name , cmd_build_fct_use , conv_regex_fct_use = out_conv_sel
    
    #### Force the cmd_build_fct, if any
    if cmd_build_fct:
        cmd_build_fct_use = cmd_build_fct

    #### Force the conv_regex_fct, if any        
    if conv_regex_fct:
        conv_regex_fct_use = cmd_build_fct    
    
    
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
