#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 14 12:05:28 2023

@author: psakicki
"""

#### Import star style
from pathlib import Path
#from pathlib3x import Path
from geodezyx import utils


def _kw_options_dict2str(kw_options):
    """
    from a dict of keywords/values, generate the corresponding 
    command line part as list and string
    
    e.g.
    kw_options["-a"] = "valueA"
    kw_options["-b"] = "42"
    returns
    '-a valueA -b 42'
    """
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
    """
    from a dict of keywords/values, generate the corresponding 
    command line part as list and string
    
    e.g.
    ["-a",Path(valueA),"-b",42] 
    returns
    '-a valueA -b 42'
    """
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
    """
    Build a command to launch a generic converter
    It has to be used for developement purposes only
    """
    
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
    """
    Build a command to launch trm2rinex, the Trimble converter
    
    It has the same behavior as all the `cmd_build` functions

    Parameters
    ----------
    inp_raw_fpath : str or Path
        the path of the input Raw GNSS file.
    out_dir : str or Path
        the path of the output directory.
    bin_options_custom : list, optional
        a list for custom option arguments. The default is [].
    bin_kwoptions_custom : dict, optional
        a dictionary for custom keywords arguments. The default is dict().
    bin_path : str, optional
        the path the executed binary.
        The default is "trm2rinex:cli-light".

    Returns
    -------
    cmd_use : list of string
        the command as a mono-string in list (singleton).
        Ready to be used by subprocess.run
    cmd_list : list of strings
        the command as a list of strings, splited for each element.
    cmd_str : string
        the command as a concatenated string.
        
    Note
    ----
    Usage of `trm2rinex`
    
    docker run --rm -v ${f_dir}:/inp -v ${DIR_out}:/out trm2rinex:cli-light inp/${f_base} -p out/${subdir_out_010} -n -d -s -v 3.04
    
    data/MAGC320b.2021.rt27 defines the input file (relative to container filesystem root)
    -p data/out defines the path for the conversion output (relative to container filesystem root)
    -n to NOT perform height reference point corrections
    -d to include doppler observables in the output observation file
    -co to include clock corrections in the output observation file
    -s to include signal strength values in the output observation file
    -v 3.04 to choose which RINEX version is generated (cf. command line usage for details)
    -h 0.1387 to include the marker to antenna ARP vertical offset into RINEX header 

    """

    #### Convert the paths as Path objects
    inp_raw_fpath = Path(inp_raw_fpath)
    out_dir = Path(out_dir)

    ### out_dir must be writable by root => 777
    out_dir_access_rights = out_dir.stat().st_mode  
    out_dir.chmod(0o777)

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
    
    """
    Build a command to launch mdb2rinex, the Leica converter
    
    It has the same behavior as all the `cmd_build` functions

    Parameters
    ----------
    inp_raw_fpath : str or Path
        the path of the input Raw GNSS file.
    out_dir : str or Path
        the path of the output directory.
    bin_options_custom : list, optional
        a list for custom option arguments. The default is [].
    bin_kwoptions_custom : dict, optional
        a dictionary for custom keywords arguments. The default is dict().
    bin_path : str, optional
        the path the executed binary.
        The default is "mdb2rinex".

    Returns
    -------
    cmd_use : list of string
        the command as a mono-string in list (singleton).
        Ready to be used by subprocess.run
    cmd_list : list of strings
        the command as a list of strings, splited for each element.
    cmd_str : string
        the command as a concatenated string.
        
    Note
    ----
    
    Usage of `mdb2rinex`
    
    Options:
    -h [ --help ]         Print help messages
    -v [ --version ]      Print program version
    -s [ --summary ]      Print tracking summary at end of obs file
    -o [ --out ] arg      Output directory
    -f [ --files ] arg    Mdb input file list
    
    """
    
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

    """
    Build a command to launch sbf2rin, the Septentrio converter
    
    It has the same behavior as all the `cmd_build` functions

    Parameters
    ----------
    inp_raw_fpath : str or Path
        the path of the input Raw GNSS file.
    out_dir : str or Path
        the path of the output directory.
    bin_options_custom : list, optional
        a list for custom option arguments. The default is [].
    bin_kwoptions_custom : dict, optional
        a dictionary for custom keywords arguments. The default is dict().
    bin_path : str, optional
        the path the executed binary.
        The default is "sbf2rin".

    Returns
    -------
    cmd_use : list of string
        the command as a mono-string in list (singleton).
        Ready to be used by subprocess.run
    cmd_list : list of strings
        the command as a list of strings, splited for each element.
    cmd_str : string
        the command as a concatenated string.
        
    Note
    ----
    Usage of `sbf2rin`
    
     sbf2rin -f input_file [-o output_file][-l][-O CCC][-R3][-R210][-n type]
                       [-MET][-i interval][-b startepoch][-e endepoch]
                       [-s][-D][-X][-c][-C commentstr][-x systems]
                       [-I siglist][-E siglist][-a antenna][-ma][-mf]
                       [-noevent][-S][-v][-V]

   -f input_file   (mandatory) Name of the SBF file(s) to be converted.
                   To convert multiple files, use a whitespace as
                   delimiter between the different file names. Each SBF
                   file is converted into a different RINEX file.
   -o output_file  Name of the output RINEX file, bypassing the standard
                   naming convention. See file naming convention below.
                   Note: do not use a forced output file name when
                   converting multiple files.
   -l              Use long file naming convention (introduced in RINEX
                   v3.02). Default is short file name. See below.
   -O CCC          Force using the specified 3-letter country code in
                   the long file name. This option is ignored if the -l
                   option is not used.
   -R version      By default, sbf2rin converts to RINEX v3.04.
                   -R211 converts to v2.11,
                   -R303 converts to v3.03,
                   -R304 converts to v3.04,
                   -R305 converts to v3.05,
                   -R400 converts to v4.00,
                   -R3 is an alias for -R304,
                   -R4 is an alias for -R400.
   -n type         Type of files to be generated.  type is a combination
                   of the following characters:
                     O for an observation file (this is the default),
                     N for a GPS-only navigation file,
                     G for a GLONASS-only navigation file,
                     E for a Galileo-only navigation file (always RINEX
                       v3.xx or above),
                     H for a SBAS-only navigation file,
                     I for a BeiDou-only navigation file (always RINEX
                       v3.xx or above),
                     P for a mixed GNSS navigation file (always RINEX
                       v3.xx or above),
                     B for a broadcast SBAS file (all L1 and L5 messages),
                       valid only for a broadcast SBAS file (valid CRC
                       only),
                     M for a meteo file.
                   Note that QZSS and IRNSS/NavIC navigation data is only
                   available in mixed files.
                   If multiple characters are combined, all the requested
                   RINEX files are generated at once. For example -nPOM
                   generates obs, mixed nav and meteo files.
   -MET            Generate a RINEX meteo file (same as -nM).
   -i interval     Interval in the RINEX obs and meteo file, in seconds
                   (by default, the interval is the same as in the SBF
                    file).
   -b startepoch   Time of first epoch to insert in the RINEX file.
                   Format: yyyy-mm-dd_hh:mm:ss or hh:mm:ss.
   -e endepoch     Last epoch to insert in the RINEX file
                   Format: yyyy-mm-dd_hh:mm:ss or hh:mm:ss.
   -s              Include the Sx obs types in the observation file.
   -D              Include the Dx obs types in the observation file.
   -X              Include the X1 obs types (channel number) in the
                   observation file.
                   (option not available when generating RINEX v2.11
                    files).
   -c              Allow comments in the RINEX file (from the Comment SBF
                   block)
   -C commentstr   Add the specified comment string to the RINEX obs
                   header. The comment string must not be longer than
                   240 characters. Enclose the string between quotes if
                   it contains whitespaces.
   -U              Make sure a satellite number does not appear more than
                   once in a given epoch, which could otherwise happen when
                   the receiver is configured to track the same satellite on
                   multiple channels, or in rare cases when two GLONASS
                   satellites are using the same slot number.
   -x systems      Exclude one or more satellite systems from the obs
                   file or from the mixed navigation file.
                   systems may be G (GPS), R (Glonass), E (Galileo), S
                   (SBAS), C (Compass/Beidou), J (QZSS), I (IRNSS/NavIC) or
                   any combination thereof. For instance, -xERSCJI produces
                   a GPS-only file.
   -I siglist      Include only the observables from the specified signal
                   types. By default all observables in the SBF file are
                   converted to RINEX. siglist is a list of signal types
                   separated by "+" and without whitespaces.  The
                   available signal types are:
                   GPSL1CA, GPSL1P, GPSL2P, GPSL2C, GPSL5, GPSL1C,
                   GLOL1CA, GLOL1P, GLOL2P, GLOL2CA, GLOL3,
                   GALE1, GALE5a, GALE5b, GALE5, GALE6,
                   BDSB1I, BDSB2I, BDSB3I, BDSB1C, BDSB2a, BDSB2b,
                   QZSL1CA, QZSL2C, QZSL5, QZSL1C, QZSL1S, QZSL5S
                   SBSL1, SBSL5,
                   IRNL5, IRNS1.
                   For example: -I GPSL1CA+GLOL1CA
   -E siglist      Exclude the observables from the specified signal
                   types. See the -I argument for a definition of siglist.
   -a antenna      Convert data from the specified antenna (antenna is 1,
                   2 or 3). The default is 1, corresponding to the main
                   antenna.
   -ma             Insert a "start moving" event right after the header
                   if the RINEX file contains kinematic data.
   -mf             Force inserting a "start moving" event right after
                   the header.
   -noevent        Do not report external events in RINEX.  Default is to
                   report external events in comment strings.
   -S              Automatically increase the file sequence character in
                   the output file name when converting multiple files
                   from the same marker and the same day. This option is
                   ignored if the -l or the -o option is also selected.
   -v              Run in verbose mode.
   -V              Display the sbf2rin version.
    """
    
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
    """
    Build a command to launch runpkr00, the Trimble > teqc converter
    
    It has the same behavior as all the `cmd_build` functions

    Parameters
    ----------
    inp_raw_fpath : str or Path
        the path of the input Raw GNSS file.
    out_dir : str or Path
        the path of the output directory.
    bin_options_custom : list, optional
        a list for custom option arguments. The default is [].
    bin_kwoptions_custom : dict, optional
        a dictionary for custom keywords arguments. The default is dict().
    bin_path : str, optional
        the path the executed binary.
        The default is "runpkr00".

    Returns
    -------
    cmd_use : list of string
        the command as a mono-string in list (singleton).
        Ready to be used by subprocess.run
    cmd_list : list of strings
        the command as a list of strings, splited for each element.
    cmd_str : string
        the command as a concatenated string.
        
    Note
    ----
    Usage of `runpkr00`
    
    runpkr00 - Utility to unpack Trimble R00\T00\T01\T02 files, Version 6.03 (Linux) ( t01lib 8.111 )
    Copyright (c) Trimble Navigation Limited 1992-2015.  All rights reserved.
    
    usage: runpkr00 [-deimacfvq] [-sfile] [-x[ehi*]] [-tfmt] [-n[!]] [-u0|1] src[+s2+s3+..+sn] [@file] [out]
      @file      file with list of files to be concatenated (one per line)
      -c         ignore checksum errors
      -a         produce APP file (when possible)
      -d         produce DAT file
      -e         produce EPH file
      -i         produce ION file
      -m         produce MES file
      -n[!]      fix NetRS serial number, [!-unconditional]
      -s[file]   produce Summary file
      -f         attempt fixup if possible
      -u[0|1]    update file name [0-dft, 1-station]
      -v         verbose
      -x[ehi*]   exclude initial: e-eph, h-header, i-ionutc, *-all
      -tfmt      format type of file (fmt=r00,t00,t01,t02)
      -q         quick summary to std out
      -g         use type 27 (if it exists) and allow extended type 17
    
    examples: runpkr00 -d gs00233a
              runpkr00 -dev gs00233a gnew233a
              runpkr00 -deimv gs00233a c:\new\gs00233a
              runpkr00 -de c:\old\gs00233a c:\new\gs00233a
              runpkr00 -demv gs00233a+gs00233b+gs00233c comb2330
              runpkr00 -demv @r00.lst comb2330
    """
    
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

    #out_fpath = out_dir.joinpath(inp_raw_fpath.with_suffix(".rnx_teqc").name)   
    out_fpath = out_dir.joinpath(inp_raw_fpath.name + ".rnx_teqc")   
    
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
                   bin_path="convbin"):    
    """
    Build a command to launch convbin, the RTKLIB converter, for BINEX
    
    It has the same behavior as all the `cmd_build` functions

    Parameters
    ----------
    inp_raw_fpath : str or Path
        the path of the input Raw GNSS file.
    out_dir : str or Path
        the path of the output directory.
    bin_options_custom : list, optional
        a list for custom option arguments. The default is [].
    bin_kwoptions_custom : dict, optional
        a dictionary for custom keywords arguments. The default is dict().
    bin_path : str, optional
        the path the executed binary.
        The default is "convbin".

    Returns
    -------
    cmd_use : list of string
        the command as a mono-string in list (singleton).
        Ready to be used by subprocess.run
    cmd_list : list of strings
        the command as a list of strings, splited for each element.
    cmd_str : string
        the command as a concatenated string.
        
    Note
    ----
    Usage of `convbin`

    convbin [option ...] file
    
    Description
    
    Convert RTCM, receiver raw data log and RINEX file to RINEX and SBAS/LEX
    message file. SBAS message file complies with RTKLIB SBAS/LEX message
    format. It supports the following messages or files.
    
    RTCM 2                : Type 1, 3, 9, 14, 16, 17, 18, 19, 22
    RTCM 3                : Type 1002, 1004, 1005, 1006, 1010, 1012, 1019, 1020
                            Type 1071-1127 (MSM except for compact msg)
    NovAtel OEMV/4,OEMStar: RANGECMPB, RANGEB, RAWEPHEMB, IONUTCB, RAWWASSFRAMEB
    u-blox LEA-4T/5T/6T/8/9  : RXM-RAW, RXM-RAWX, RXM-SFRB
    Swift Piksi Multi     : 
    Hemisphere            : BIN76, BIN80, BIN94, BIN95, BIN96
    SkyTraq S1315F        : msg0xDD, msg0xE0, msg0xDC
    GW10                  : msg0x08, msg0x03, msg0x27, msg0x20
    Javad                 : [R*],[r*],[*R],[*r],[P*],[p*],[*P],[*p],[D*],[*d],
                            [E*],[*E],[F*],[TC],[GE],[NE],[EN],[QE],[UO],[IO],
                            [WD]
    NVS                   : BINR
    BINEX                 : big-endian, regular CRC, forward record (0xE2)
                            0x01-01,0x01-02,0x01-03,0x01-04,0x01-06,0x7f-05
    Trimble               : RT17
    Septentrio            : SBF
    RINEX                 : OBS, NAV, GNAV, HNAV, LNAV, QNAV
    
    Options [default]
    
        file         input receiver binary log file
        -ts y/m/d h:m:s  start time [all]
        -te y/m/d h:m:s  end time [all]
        -tr y/m/d h:m:s  approximated time for RTCM
        -ti tint     observation data interval (s) [all]
        -tt ttol     observation data epoch tolerance (s) [0.005]
        -span span   time span (h) [all]
        -r format    log format type
                      rtcm2= RTCM 2
                      rtcm3= RTCM 3
                      nov  = NovAtel OEM/4/V/6/7,OEMStar
                      ubx  = ublox LEA-4T/5T/6T/7T/M8T/F9
                      sbp  = Swift Navigation SBP
                      hemis= Hemisphere Eclipse/Crescent
                      stq  = SkyTraq S1315F
                      javad= Javad GREIS
                      nvs  = NVS NV08C BINR
                      binex= BINEX
                      rt17 = Trimble RT17
                      sbf  = Septentrio SBF
                      rinex= RINEX
        -ro opt      receiver options
        -f freq      number of frequencies [5]
        -hc comment  rinex header: comment line
        -hm marker   rinex header: marker name
        -hn markno   rinex header: marker number
        -ht marktype rinex header: marker type
        -ho observ   rinex header: oberver name and agency separated by /
        -hr rec      rinex header: receiver number, type and version separated by /
        -ha ant      rinex header: antenna number and type separated by /
        -hp pos      rinex header: approx position x/y/z separated by /
        -hd delta    rinex header: antenna delta h/e/n separated by /
        -v ver       rinex version [3.04]
        -od          include doppler frequency in rinex obs [on]
        -os          include snr in rinex obs [on]
        -oi          include iono correction in rinex nav header [off]
        -ot          include time correction in rinex nav header [off]
        -ol          include leap seconds in rinex nav header [off]
        -halfc       half-cycle ambiguity correction [off]
        -mask   [sig[,...]] signal mask(s) (sig={G|R|E|J|S|C|I}L{1C|1P|1W|...})
        -nomask [sig[,...]] signal no mask (same as above)
        -x sat       exclude satellite
        -y sys       exclude systems (G:GPS,R:GLO,E:GAL,J:QZS,S:SBS,C:BDS,I:IRN)
        -d dir       output directory [same as input file]
        -c staid     use RINEX file name convention with staid [off]
        -o ofile     output RINEX OBS file
        -n nfile     output RINEX NAV file
        -g gfile     output RINEX GNAV file
        -h hfile     output RINEX HNAV file
        -q qfile     output RINEX QNAV file
        -l lfile     output RINEX LNAV file
        -b cfile     output RINEX CNAV file
        -i ifile     output RINEX INAV file
        -s sfile     output SBAS message file
        -trace level output trace level [off]
    
    If any output file specified, default output files (<file>.obs,
    <file>.nav, <file>.gnav, <file>.hnav, <file>.qnav, <file>.lnav,
    <file>.cnav, <file>.inav and <file>.sbs) are used. To obtain week number info
    for RTCM file, use -tr option to specify the approximated log start time.
    Without -tr option, the program obtains the week number from the time-tag file (if it exists) or the last modified time of the log file instead.
    
    If receiver type is not specified, type is recognized by the input
    file extension as follows.
        *.rtcm2       RTCM 2
        *.rtcm3       RTCM 3
        *.gps         NovAtel OEM4/V/6/7,OEMStar
        *.ubx         u-blox LEA-4T/5T/6T/7T/M8T/F9
        *.sbp         Swift Navigation SBP
        *.bin         Hemisphere Eclipse/Crescent
        *.stq         SkyTraq S1315F
        *.jps         Javad GREIS
        *.bnx,*binex  BINEX
        *.rt17        Trimble RT17
        *.sbf         Septentrio SBF
        *.obs,*.*o    RINEX OBS
        *.rnx         RINEX OBS     *.nav,*.*n    RINEX NAV
    """
    
    #### Convert the paths as Path objects
    inp_raw_fpath = Path(inp_raw_fpath)
    out_dir = Path(out_dir)
    
    cmd_opt_list , _ = _options_list2str(bin_options_custom)
    cmd_kwopt_list , _ = _kw_options_dict2str(bin_kwoptions_custom)
    
    cmd_list = [bin_path,'-d',out_dir,'-os','-od','-r','binex'] + cmd_opt_list + cmd_kwopt_list + [inp_raw_fpath]
    cmd_list = [str(e) for e in cmd_list]
    cmd_str = " ".join(cmd_list)
    cmd_use = [cmd_str]
    
    return cmd_use, cmd_list, cmd_str

def cmd_build_tps2rin(inp_raw_fpath,
                      out_dir,
                      bin_options_custom=[],
                      bin_kwoptions_custom=dict(),
                      bin_path="/opt/softs_gnss/bin/tps2rin.exe"):
    """
    Build a command to launch tps2rin, for Topcon
    
    It has the same behavior as all the `cmd_build` functions

    Parameters
    ----------
    inp_raw_fpath : str or Path
        the path of the input Raw GNSS file.
    out_dir : str or Path
        the path of the output directory.
    bin_options_custom : list, optional
        a list for custom option arguments. The default is [].
    bin_kwoptions_custom : dict, optional
        a dictionary for custom keywords arguments. The default is dict().
    bin_path : str, optional
        the path the executed binary.
        The default is "tps2rin".

    Returns
    -------
    cmd_use : list of string
        the command as a mono-string in list (singleton).
        Ready to be used by subprocess.run
    cmd_list : list of strings
        the command as a list of strings, splited for each element.
    cmd_str : string
        the command as a concatenated string.
        
    Note
    ----
    Usage of `tps2rin`
    
    TPS2RIN 1.0.28.3459 Win64 build Jun 01, 2022 (c) Topcon Positioning Systems
    Conversion of TPS file to RINEX.
    Usage :  TPS2RIN  [<sw> [ <sw>]]  <input file name> [<sw> [ <sw>]]
    <Switches(sw)>:
      -h, -?, --help     Display help screen.
      -v <version>       Set RINEX version. Valid are 2.10, 2.11, 2.12, 3.00, 3.01, 3
    .02, 3.03, 3.04, 3.05, 4.00 versions.
                        Default version is 3.05.
      -o <output dir>    Output directory. Current directory used by default.
      -p <Profile name>  For detailed help type 'TPS2RIN -p ?'.
      -i <input file>    Specify input file name. Required if <input file> starts wit
    h '-' or '+'.
      -s <StartTime>     Start date/time. For detailed help type 'TPS2RIN -s ?'.
      -f <FinishTime>    Finish date/time. For detailed help type 'TPS2RIN -f ?'.
      --date <CurrTime>  Current date/time. For detailed help type 'TPS2RIN --date ?'
    .
      -G                 Exclude all GPS satellites.
      -G<nn>,-g <nn>     Exclude GPS satellite G##.
      +G<nn>,+g <nn>     Include GPS satellite G## (used after -G).
      -R                 Exclude all GLONASS satellites.
      -R<nn>,-r <nn>     Exclude GLONASS satellite R##.
      +R<nn>,+r <nn>     Include GLONASS satellite R## (used after -R).
      -E                 Exclude all GALILEO satellites.
      -E<nn>             Exclude GALILEO satellite E##.
      +E<nn>             Include GALILEO satellite E## (used after -E).
      -C                 Exclude all BeiDou satellites.
      -C<nn>             Exclude BeiDou satellite C##.
      +C<nn>             Include BeiDou satellite C## (used after -C).
      -W                 Exclude all SBAS (WAAS) satellites, including QZSS 183-192.
      -W<nn>,-S<nn>,-w <nn> Exclude SBAS (WAAS) satellite. Use Rinex ID or PRN: S20-S
    58 or S120-S158.
      +W<nn>,+S<nn>,+w <nn> Include SBAS (WAAS) satellite (used after -W). Use Rinex 
    ID or PRN: S20-S58 or S120-S158.
      -J                 Exclude all QZSS satellites.
      -J<nn>             Exclude QZSS satellite J##. Use Rinex ID or PRN: J01-J10, J1
    93-J202, J183-J192.
      +J<nn>             Include QZSS satellite J## (used after -J). Use Rinex ID or 
    PRN: J01-J10, J193-J202, J183-J192.
      -IRN               Exclude all IRNSS satellites.
      -IRN7              7 IRNSS satellites support only.
      -I<nn>             Exclude IRNSS satellite I##.
      +I<nn>             Include IRNSS satellite I## (used after -IRN).
      -1,-2,..,-5, ..,-9 Exclude all selected band measurements from output RINEX. (F
    or example, -1 exludes C1, L1, P1, D1, S1).
      -C2                Ignore all L2C channel measurements (GPS/GLONASS only).
      --no-L1C           Ignore L1-C/A carrier phase/doppler/SNR (GPS/GLONASS only).
      --no-L1P           Ignore L1-P carrier phase/doppler/SNR (GPS/GLONASS only).
      --no-L2C           Ignore L2-C/A carrier phase/doppler/SNR (GPS/GLONASS only).
      --no-L2P           Ignore L2-P carrier phase/doppler/SNR (GPS/GLONASS only).
      --no-C1C           Ignore L1-C/A pseudorange (GPS/GLONASS only).
      --no-C1P           Ignore L1-P pseudorange (GPS/GLONASS only).
      --no-C2C           Ignore L2-C/A pseudorange (GPS/GLONASS only).
      --no-C2P           Ignore L2-P pseudorange (GPS/GLONASS only).
      --no-rM            Skip rM messages. Same as --skip rM.
      --no-rD            Skip rD messages. Same as --skip rD.
      --no-rL            Skip rL messages. Same as --skip rL.
      --no-rS            Skip rS messages. Same as --skip rS.
      --use-rM           Ignore all regular TPS messages, use rM messages.
      --use-rD           Ignore all regular TPS messages, use rD messages.
      --skip <Id[,Id]>   Skip list of TPS messages.
      -I <sec>           Interval in seconds. Floating point value is OK.
      -L <n>             If Leap Seconds information is missing, force Leap Seconds t
    o <n>.
      -D                 Exclude Doppler.
      -O                 Include Receiver Clock Offset in epoch header lines.
      --apply-clock-bias Apply Receiver Clock Offset to epoch time, carrier phases an
    d pseudoranges.
      --keep-epoch-time  Option --apply-clock-bias applied to carrier phases and pseu
    doranges using doppler.
      -S                 Include observation types S1,S2. Units: dB*Hz.
      -~                 Apply Smoothing to pseudoranges.
      -M <Name>          Override any Marker Name found in profile or input file.
      -m <Number>        Override any Marker Number found in profile or input file.
      -T <Type>          Override any Marker Type found in profile (GEODETIC and NON_
    GEODETIC mean static survey mode).
      -A <Name>          Override Antenna type name. For details type 'TPS2RIN -A ?'.
      -a <Number>        Override Antenna Serial # found in profile or input file.
      --slant <r>,<v>    Convert antenna height from SLANT to VERTICAL: r - radius, m
    m; v - C1-A1, mm.
      --meteo-model <model>
      -Met.Model <model> Override Meteo Device Model found in profile.
      --meteo-type <type>
      -Met.Type <type>   Override Meteo Device Type found in profile.
      --sn               Prefer to output receiver serial number instead of receiver 
    id.
      -=                 Ignore User Events. For details type .TPS2RIN -= ?'.
      -XYZ <X> <Y> <Z>   Override approximate XYZ calculated from raw position or giv
    en in profile.
      -c                 Use Hatanaka Compression.
      -N <ABCD>          Short Marker Name alias for Marker Name.
      --lfn <R,CAN,00>   Use long file name format. R is data source, CAN - country c
    ode,
                        00 - station code (monument 0-9 and receiver 0-9 numbers).
      --file-period <n>  Rotation File period in seconds for file name generation.
      --doi              Digital Object Identifier (DOI) for data citation.
      --license          Name of the license or link to the specific version of the l
    icense.
      --station-info     The link to persistent URL with the station metadata.
      --no-cnav          Don't use common navigational file for RINEX 3.0.
      --no-obs           Don't create observation file.
      --no-eph           Don't create ephemeris files.
      --no-meteo         Don't create meteo file.
      --no-tilt          Don't create angular file.
      --no-extra         Don't create any extra files except observation and ephemeri
    s.
      --sort             Sort satellites in epochs.
      --keep-eph         Keep all present ephemeris.
      --sort-eph         Sort ephemeris by satellites and time.
      --binex            Input stream contains BINEX messages.
      --binex-use <##>   Select measurements from given subrecord ## of record 7F.
                        Subrecords 00, 02, 03 and 05 are supported.
      --binex-skip <##>  Skip record ##. May use several times.
      --binex-7F05-fmt   Format for record 7F subrecord 05 RxClkOff field.
                        Valid values are "s+21b" or "2c22b" (default).
      --log <log file>   Write log file. Use '-' for writing to stdout.
      --preview          Scan the file and print a short summary.
      --print            Print all TPS messages to the log file.
      --utf8             Log file has UTF-8 charset.
    """
    
    #### Convert the paths as Path objects
    inp_raw_fpath = Path(inp_raw_fpath)
    out_dir = Path(out_dir)
    
    cmd_opt_list , _ = _options_list2str(bin_options_custom)
    cmd_kwopt_list , _ = _kw_options_dict2str(bin_kwoptions_custom)
    
    cmd_list = ['wine',bin_path,'-o',out_dir] + cmd_opt_list + cmd_kwopt_list + ['-i',inp_raw_fpath]
    cmd_list = [str(e) for e in cmd_list]
    cmd_str = " ".join(cmd_list)
    cmd_use = [cmd_str]
    
    return cmd_use, cmd_list, cmd_str
    




