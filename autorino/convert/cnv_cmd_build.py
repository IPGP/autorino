#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 14 12:05:28 2023cd

@author: psakic

This module contains the functions to build the generic commands 
needed to run a GNSS conversion

one function per converter, one  converter per manufacturer

all the functions here have the same returns:

Returns
-------
cmd_use : list of string
    the command as a mono-string in list (singleton).
    Ready to be used by subprocess.run
cmd_list : list of strings
    the command as a list of strings, splited for each element.
cmd_str : string
    the command as a concatenated string.


"""

# Import star style
from pathlib import Path

# from pathlib3x import Path
from geodezyx import utils

# IMPORT AUTORINO ENVIRONNEMENT VARABLES
##software paths
import autorino.cfgenv.env_read as aroenv

aro_env_soft_path = aroenv.ARO_ENV_DIC["conv_software_paths"]


def _kw_options_dict2str(kw_options):
    """
    Converts a dictionary of keyword options into a command line string.

    This function takes a dictionary where the keys are command line option flags (e.g., "-a", "-b")
    and the values are the corresponding values for these flags.
    It returns a string that represents these options in a format that can be used in a command line interface.

    Parameters
    ----------
    kw_options : dict
        A dictionary where the keys are command line option flags and the values
        are the corresponding values for these flags.

    Returns
    -------
    cmd_list : list
        A list where the elements are command line options and their values.
    cmd_str : str
        A string that represents the command line options and their values.

    Examples
    --------
    >>> kw_options = {"-a": "valueA", "-b": "42"}
    >>> _kw_options_dict2str(kw_options)
    '-a valueA -b 42'
    """
    cmd_list = []

    if utils.is_iterable(kw_options):
        pass
    else:
        kw_options = [kw_options]

    for kwo in kw_options:
        for key, val in kwo.items():
            cmd_list = cmd_list + [str(key), str(val)]

    cmd_str = " ".join(cmd_list)

    return cmd_list, cmd_str


def _options_list2str(options):
    """
    Converts a list of options into a command line string.

    This function takes a list where the elements are command line options
    (e.g., "-a", Path(valueA), "-b", 42) and returns a string that represents these options
    in a format that can be used in a command line interface.

    Parameters
    ----------
    options : list
        A list where the elements are command line options.

    Returns
    -------
    cmd_list : list of str
        A list where the elements are command line options and their values.
    cmd_str : str
        A string that represents the command line options and their values.

    Examples
    --------
    > options = ["-a", Path(valueA), "-b", 42]
    > _options_list2str(options)
    (['-a', 'valueA', '-b', '42'], '-a valueA -b 42')
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


def cmd_build_generic(
    program="",
    options=[""],
    kw_options=dict(),
    arguments="",
    options_bis=[""],
    kw_options_bis=dict(),
):
    """
    Builds a command to launch a generic converter.

    This function is primarily used for development purposes.
    It constructs a command by concatenating the provided parameters in a specific order.
    The command can then be used to launch a generic converter.

    Parameters
    ----------
    program : str, optional
        The name of the program or converter to be launched. Default is an empty string.
    options : list, optional
        A list of options to be passed to the program. Default is an empty list.
    kw_options : dict, optional
        A dictionary of keyword options to be passed to the program. Default is an empty dictionary.
    arguments : str, optional
        The arguments to be passed to the program. Default is an empty string.
    options_bis : list, optional
        A second list of options to be passed to the program. Default is an empty list.
    kw_options_bis : dict, optional
        A second dictionary of keyword options to be passed to the program. Default is an empty dictionary.

    Returns
    -------
    list
        The constructed command as a list of strings.
    """

    cmd = []

    if utils.is_iterable(program):
        cmd = [str(e) for e in program]
    else:
        cmd = [str(program)]

    for key, val in kw_options.items():
        cmd = cmd + [str(key), str(val)]

    for key, val in kw_options_bis.items():
        cmd = cmd + [str(key), str(val)]

    if utils.is_iterable(arguments):
        arguments = [str(e) for e in arguments]
    else:
        arguments = [str(arguments)]

    cmd = cmd + options + options_bis + arguments

    cmd_str = " ".join(cmd)

    return cmd, cmd_str


def cmd_build_trm2rinex(
    inp_raw_fpath,
    out_dir,
    bin_options_custom=[],
    bin_kwoptions_custom=dict(),
    bin_path=aro_env_soft_path["trm2rinex"],
):
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

    docker run --rm -v ${DIR_INP}:/inp -v ${DIR_OUT}:/out trm2rinex:cli-light
    inp/${FNAME_RAW} -p out/${SUBDIR_OUT} -n -d -s -v 3.04

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

    # out_dir must be writable by root => 777
    out_dir_access_rights = out_dir.stat().st_mode
    out_dir.chmod(0o777)

    cmd_docker_list = [
        "docker",
        "run",
        "--rm",
        "-v",
        str(inp_raw_fpath.parent.resolve()) + ":/inp",
        "-v",
        str(out_dir.resolve()) + ":/out",
    ]
    cmd_trm2rinex_list = [
        bin_path,
        "inp/" + inp_raw_fpath.name,
        "-n",
        # "-d", # doppler disabled, because can cause non standard values for RINEX format
        "-s",
        "-v",
        "3.04",
        "-p",
        "out/",
    ]

    cmd_opt_list, _ = _options_list2str(bin_options_custom)
    cmd_kwopt_list, _ = _kw_options_dict2str(bin_kwoptions_custom)

    cmd_list = cmd_docker_list + cmd_trm2rinex_list + cmd_opt_list + cmd_kwopt_list
    cmd_list = [str(e) for e in cmd_list]
    cmd_str = " ".join(cmd_list)
    cmd_use = [cmd_str]

    return cmd_use, cmd_list, cmd_str


def cmd_build_t0xconvert(
    inp_raw_fpath,
    out_dir,
    bin_options_custom=[],
    bin_kwoptions_custom=dict(),
    bin_path=aro_env_soft_path["t0xconvert"],
):
    """
    Build a command to launch t0xConvert, the Trimble converter

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
        The default is "t0xConvert".

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

    Usage of `t0xConvert`

    t0xConvert - Utility to convert Trimble T02/T04 files to RINEX
    Version 2.38.0. Copyright (c) Trimble Inc. 2008-2023.  All rights reserved


    Usage: t0xConvert {file_options} [field_options] <input_file>

    <input_file>       Trimble T02/T04 format file

    File_options:
    -o                 Specifying "-o" creates a RINEX observation file
    -ofixed            Use fixed # of observation fields with -o
    -h                 Specifying "-h" creates a Hatanaka compressed observation file
    -nNAV              File Type
                        -ngps      - GPS NAV file
                        -nglonass  - GLONASS NAV file
                        -ngalileo  - GALILEO NAV file
                        -nqzss     - QZSS NAV file
                        -ncombined - Combined NAV file
    -m                 Create MET file
    -vVER              RINEX Version x100 (default 211)
                        Supported Formats
                        211 = RINEX 2.11
                        212 = RINEX 2.12 with QZSS extensions
                        300 = RINEX 3.00
                        302 = RINEX 3.02
                        303 = RINEX 3.03
                        304 = RINEX 3.04
                        e.g. -v304 will generate output files in RINEX 3.04 format
    -z                 Zip up all generated files into one zip file

    Field_options:
      The form for field options is <specifier>=<value>, so to override the
      AGENCY field to be "Trimble", you would use -ag="Trimble". Here are the
      supported <specifier> types:

    -ob                Observer,          e.g. -ob="BILL SMITH"
    -ag                Agency,            e.g. -ag="ABC INSTITUTE"
    -rb                Run By,            e.g. -rb="BILL SMITH"
    -mo                Marker Name,       e.g. -mo="A 9080"
    -mn                Marker Number      e.g. -mn="9080.1.34"
    -at                Antenna Type       e.g. -at="ROVER"
    -an                Antenna Number     e.g. -an="G1234"
    -ah                Antenna Height     e.g. -ah="0.01"
    -rt                Receiver Type      e.g. -rt="GEODETIC"
    -rn                Receiver Number    e.g. -rn="X1234A1234"
    -ap                Approx. XYZ Position. Use ',' to separate X, Y, and Z
                       values as in the following example:
                       -ap=-2689320.68662,-4302891.91205,3851423.71881
    """

    # Convert the paths as Path objects
    inp_raw_fpath = Path(inp_raw_fpath)
    out_dir = Path(out_dir)

    inp_raw_fpath_tmp = Path.joinpath(out_dir, inp_raw_fpath.name)
    # Copy the input file to the output directory (this is done silentely)
    # shutil.copy(inp_raw_fpath, inp_raw_fpath_tmp)
    # this is actually done with a shell cp command prior to the conversion
    # see the cmd_list below

    cmd_opt_list, _ = _options_list2str(bin_options_custom)
    cmd_kwopt_list, _ = _kw_options_dict2str(bin_kwoptions_custom)

    cmd_list = (
        ["cp", str(inp_raw_fpath), str(out_dir), "&&"]
        + [bin_path, "-o", "-v304"]
        + cmd_opt_list
        + cmd_kwopt_list
        + [str(inp_raw_fpath_tmp)]
    )
    cmd_list = [str(e) for e in cmd_list]
    cmd_str = " ".join(cmd_list)
    cmd_use = [cmd_str]

    # Remove the temporary file (this is done silentely)
    # os.remove(inp_raw_fpath_tmp)

    return cmd_use, cmd_list, cmd_str


def cmd_build_mdb2rinex(
    inp_raw_fpath,
    out_dir,
    bin_options_custom=[],
    bin_kwoptions_custom=dict(),
    bin_path=aro_env_soft_path["mdb2rinex"],
):
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

    # Convert the paths as Path objects
    inp_raw_fpath = Path(inp_raw_fpath)
    out_dir = Path(out_dir)

    cmd_opt_list, _ = _options_list2str(bin_options_custom)
    cmd_kwopt_list, _ = _kw_options_dict2str(bin_kwoptions_custom)

    cmd_list = (
        [bin_path, "--out", out_dir, "--files", inp_raw_fpath]
        + cmd_opt_list
        + cmd_kwopt_list
    )
    cmd_list = [str(e) for e in cmd_list]
    cmd_str = " ".join(cmd_list)
    cmd_use = [cmd_str]

    return cmd_use, cmd_list, cmd_str


def cmd_build_sbf2rin(
    inp_raw_fpath,
    out_dir,
    bin_options_custom=[],
    bin_kwoptions_custom=dict(),
    bin_path=aro_env_soft_path["sbf2rin"],
):
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

    # Convert the paths as Path objects
    inp_raw_fpath = Path(inp_raw_fpath)
    out_dir = Path(out_dir)

    cmd_opt_list, _ = _options_list2str(bin_options_custom)
    cmd_kwopt_list, _ = _kw_options_dict2str(bin_kwoptions_custom)

    out_fpath = out_dir.joinpath(inp_raw_fpath.name + ".rnx_sbf2rin")

    cmd_list = (
        [bin_path, "-f", inp_raw_fpath, "-o", out_fpath, "-s"]
        + cmd_opt_list
        + cmd_kwopt_list
    )
    cmd_list = [str(e) for e in cmd_list]
    cmd_str = " ".join(cmd_list)
    cmd_use = [cmd_str]

    return cmd_use, cmd_list, cmd_str


def cmd_build_runpkr00(
    inp_raw_fpath,
    out_dir,
    bin_options_custom=[],
    bin_kwoptions_custom=dict(),
    bin_path=aro_env_soft_path["runpkr00"],
):
    """
    Build a command to launch runpkr00, the Trimble > teqc converter

    It has the same behavior as all th<e `cmd_build` functions

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

    runpkr00 - Utility to unpack Trimble R00, T00, T01, T02 files, Version 6.03 (Linux) ( t01lib 8.111 )
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
              runpkr00 -deimv gs00233a c:\\new\\gs00233a
              runpkr00 -de c:\\old\\gs00233a c:\new\\gs00233a
              runpkr00 -demv gs00233a+gs00233b+gs00233c comb2330
              runpkr00 -demv @r00.lst comb2330
    """

    # Convert the paths as Path objects
    inp_raw_fpath = Path(inp_raw_fpath)
    out_dir = Path(out_dir)

    cmd_opt_list, _ = _options_list2str(bin_options_custom)
    cmd_kwopt_list, _ = _kw_options_dict2str(bin_kwoptions_custom)

    cmd_list = (
        [bin_path, "-g", "-d"]
        + cmd_opt_list
        + cmd_kwopt_list
        + [inp_raw_fpath, out_dir]
    )
    cmd_list = [str(e) for e in cmd_list]
    cmd_str = " ".join(cmd_list)
    cmd_use = [cmd_str]

    return cmd_use, cmd_list, cmd_str


def cmd_build_convbin(
    inp_raw_fpath,
    out_dir,
    bin_options_custom=[],
    bin_kwoptions_custom=dict(),
    bin_path=aro_env_soft_path["convbin"],
):
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

    cmd_opt_list, _ = _options_list2str(bin_options_custom)
    cmd_kwopt_list, _ = _kw_options_dict2str(bin_kwoptions_custom)

    cmd_list = (
        [bin_path, "-d", out_dir, "-os", "-od", "-r", "binex"]
        + cmd_opt_list
        + cmd_kwopt_list
        + [inp_raw_fpath]
    )
    cmd_list = [str(e) for e in cmd_list]
    cmd_str = " ".join(cmd_list)
    cmd_use = [cmd_str]

    return cmd_use, cmd_list, cmd_str


def cmd_build_tps2rin(
    inp_raw_fpath,
    out_dir,
    bin_options_custom=[],
    bin_kwoptions_custom=dict(),
    bin_path=aro_env_soft_path["tps2rin"],
):
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
        Since tps2rin is a Windows executable and executed with wine,
        it must be an **absoulte** path.


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

    tps2rin requires wine to run on Linux.


    Usage of `tps2rin`
    ```
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
      --lfn <R,CAN,00>   Use long file name format. R is data src, CAN - country c
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
    ```
    """

    # Convert the paths as Path objects
    inp_raw_fpath = Path(inp_raw_fpath)
    out_dir = Path(out_dir)

    cmd_opt_list, _ = _options_list2str(bin_options_custom)
    cmd_kwopt_list, _ = _kw_options_dict2str(bin_kwoptions_custom)

    cmd_list = (
        ["wine", bin_path, "-o", out_dir]
        + cmd_opt_list
        + cmd_kwopt_list
        + ["-i", inp_raw_fpath]
    )
    cmd_list = [str(e) for e in cmd_list]
    cmd_str = " ".join(cmd_list)
    cmd_use = [cmd_str]

    return cmd_use, cmd_list, cmd_str


def cmd_build_teqc(
    inp_raw_fpath,
    out_dir,
    bin_options_custom=[],
    bin_kwoptions_custom=dict(),
    bin_path=aro_env_soft_path["teqc"],
):
    """
    Build a command to launch teqc, for legacy conversion and RINEX Handeling

    It has the same behavior as all the `cmd_build` functions

    Parameters
    ----------
    inp_raw_fpath : str or Path
        the path of the input Raw GNSS file.
        for RINEX Handeling (e.g. splice) a list of path is allowed.
    out_dir : str or Path
        the path of the output directory.
    bin_options_custom : list, optional
        a list for custom option arguments. The default is [].
    bin_kwoptions_custom : dict, optional
        a dictionary for custom keywords arguments. The default is dict().
    bin_path : str, optional
        the path the executed binary.
        The default is "teqc".

    Returns
    -------
    cmd_use : list of string
        the command as a mono-string in list (singleton).
        Ready to be used by subprocess.run
    cmd_list : list of strings
        the command as a list of strings, splited for each element.
    cmd_str : string
        the command as a concatenated string.
    """

    # Convert the paths as Path objects
    out_dir = Path(out_dir)
    # for RINEX handeling, inp_raw_fpath can ben an iterable (list)
    if utils.is_iterable(inp_raw_fpath):
        raw_fpath_multi = [Path(e) for e in inp_raw_fpath]
        raw_fpath_mono = raw_fpath_multi[0]
    else:  # a single  file, most common case
        raw_fpath_multi = [Path(inp_raw_fpath)]
        raw_fpath_mono = Path(inp_raw_fpath)

    raw_fpath_str_lst = [str(e) for e in raw_fpath_multi]
    out_fpath = out_dir.joinpath(raw_fpath_mono.name + ".rnx_teqc")

    cmd_opt_list, _ = _options_list2str(bin_options_custom)
    cmd_kwopt_list, _ = _kw_options_dict2str(bin_kwoptions_custom)

    cmd_list = (
        [bin_path, "+out", out_fpath]
        + cmd_opt_list
        + cmd_kwopt_list
        + raw_fpath_str_lst
    )
    cmd_list = [str(e) for e in cmd_list]
    cmd_str = " ".join(cmd_list)
    cmd_use = [cmd_str]

    return cmd_use, cmd_list, cmd_str


def cmd_build_converto(
    inp_raw_fpath,
    out_dir,
    bin_options_custom=[],
    bin_kwoptions_custom=dict(),
    bin_path=aro_env_soft_path["converto"],
):
    """
     Build a command to launch teqc, for legacy conversion and RINEX Handeling

     It has the same behavior as all the `cmd_build` functions

     Parameters
     ----------
     inp_raw_fpath : str or Path
         the path of the input Raw GNSS file.
         for RINEX Handeling (e.g. splice) a list of path is allowed.
     out_dir : str or Path
         the path of the output directory.
     bin_options_custom : list, optional
         a list for custom option arguments. The default is [].
     bin_kwoptions_custom : dict, optional
         a dictionary for custom keywords arguments. The default is dict().
     bin_path : str, optional
         the path the executed binary.
         The default is "converto".

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

     Usage of `converto`

     ##############################################################
    "Converto" v1.0.5.2 permet d'effectuer plusieurs types de traitements sur des fichiers RINEX, dont :
    edition, extraction d'informations, conversion et controle qualite.

     ## Parametre obligatoire :
        -i[n] fichier            Nom(s) de fichier(s) en entree (separes par une virgule si plusieurs)
                                 Les caract�res regex impliquent des guillements ex : rinex.17o,"*.18o")

     ## Autres parametres :
        -o[ut] fichier           Nom(s) de fichier(s) en sortie (separes par une virgule si plusieurs)
        -cfgfiles fichier          Nom(s) de fichier(s) de configuration (separes par une virgule si plusieurs)
        -h[elp]                  Affiche ces lignes d'aide
        -ver                     Affiche le numero de version de Converto
        -a[lerte]                Active l'affichage des alertes concernant le traitement dans la console
        -v[erbose]               Active l'affichage des etapes du traitement en plus des alertes dans la console
        -rep[ort]                Ecrit un fichier de rapport (mode -cat, -conv et -ech seulement)
        -phc                     Supprime les commentaires situes apres la fin du header

                                 Mode edition par defaut
        -cat                     Mode concatenation de fichiers
        -mix                     Mode mixage de 2 fichiers RINEX OBS
        -conv                    Mode conversion V3 vers V2
        -info                    Mode extraction d'informations
        -qc                      Mode controle qualite de fichiers RINEX OBS

        -G|gps                   Exclut le systeme GPS du traitement (inclus par defaut)
        -R|glo                   Exclut le systeme GLONASS du traitement (inclus par defaut)
        -E|gal                   Exclut le systeme Galileo du traitement (inclus par defaut)
        -S|sba                   Exclut le systeme SBAS du traitement (inclus par defaut)
        -C|bds                   Exclut le systeme BDS/Compass du traitement (inclus par defaut, sauf mode -conv : voir -v212)
        -J|qzs                   Exclut le systeme QZSS du traitement (inclus par defaut, sauf mode -conv : voir -v212)
        -I|irnss                 Exclut le systeme IRNSS du traitement (inclus par defaut, sauf mode -conv : voir -v212)

     # Options d'edition de RINEX OBS ou MET :
        -st[art_window] str      set windowing start time to str == [[[[[[YY]YY]MM]DD]hh]mm]ss[.sssss]
        -e[nd_window] str        set windowing end time to str == [[[[[[YY]YY]MM]DD]hh]mm]ss[.sssss]
        -dX #                    delta X time of # from windowing start time; X == Y, M, d, h, m, s for year,...,second
                                      if negative, from windowing end time.
        -hole fichier            read file 'name' to establish list of window holes
        -tbin # str              time binned output with # time-delta (# = <N>[d|h|m|s]) and filename prefix 'str'
        -ast str                 set aligned time binned start time to str == [[[[[[YY]YY]MM]DD]hh]mm]ss[.sssss]
                                      or str = _ to start alignment with the first observation epoch

     # Options d'edition de RINEX OBS :
        -O.s[ystem] #            set RINEX OBS header satellite system to # (= G, R, E, S, C, J or M)
        -O.r[un_by] 'str'        set RINEX OBS header run by to 'str'
        -O.c[omment] 'str'       append RINEX OBS header comment 'str'
        -O.mo[nument] 'str'      set RINEX OBS header monument name to 'str'
        -O.mn 'str'              set RINEX OBS header monument number to 'str'
        -O.o[perator] 'str'      set RINEX OBS header operator name to 'str'
        -O.ag[ency] 'str'        set RINEX OBS header operating agency to 'str'
        -O.rn 'str'              set RINEX OBS header receiver number to 'str'
        -O.rt 'str'              set RINEX OBS header receiver type to 'str'
        -O.rv 'str'              set RINEX OBS header receiver firmware version to 'str'
        -O.an 'str'              set RINEX OBS header antenna number to 'str'
        -O.at 'str'              set RINEX OBS header antenna type (and radome type) to 'str'
        -O.px[WGS84xyz,m] x y z  set RINEX OBS header antenna WGS 84 position to x y z (meters)
        -O.mov[ing] 1            force RINEX OBS antenna position to be in kinematic (roving) state initially
        -O.def_wf i j            set RINEX OBS header default wavelength factors to i and j
        -O.leap #                set RINEX OBS header leap seconds to #
        -ech|O.dec[imate] #      modulo decimation of OBS epochs to # time units
                                      # = 15s results in epochs at 00, 15, 30, and 45 seconds
        -nbobs                   write or update  PRN / # OF OBS fields in the header

     # Options d'edition de RINEX OBS V2 :
        -O.obs[_types] 'str'     change RINEX OBS header observables to 'str'
                                      'str' = L1+L2+C1+P2 (or L1L2C1P2) sets 4 observables to be L1 L2 C1 P2, and in that order
        -O._obs[_types] 'str'    exclude those RINEX OBS observables listed in 'str'

     # Options d'edition de RINEX OBS V3 :
        -O.obs_G 'str'           change GPS RINEX OBS header observables to 'str'
                                      'str' = L1C+L2W+C1C+C2W sets 4 observables to be L1C L2W C1C C2W, and in that order
        -O.obs_R 'str'           change GLONASS RINEX OBS header observables to 'str'
        -O.obs_E 'str'           change Galileo RINEX OBS header observables to 'str'
        -O.obs_S 'str'           change SBAS RINEX OBS header observables to 'str'
        -O.obs_C 'str'           change BDS/Compass RINEX OBS header observables to 'str'
        -O.obs_J 'str'           change QZSS RINEX OBS header observables to 'str'
        -O.obs_I 'str'           change IRNSS RINEX OBS header observables to 'str'
        -O._obs_G 'str'          exclude those GPS RINEX OBS observables listed in 'str'
        -O._obs_R 'str'          exclude those GLONASS RINEX OBS observables listed in 'str'
        -O._obs_E 'str'          exclude those Galileo RINEX OBS observables listed in 'str'
        -O._obs_S 'str'          exclude those SBAS RINEX OBS observables listed in 'str'
        -O._obs_C 'str'          exclude those BDS/Compass RINEX OBS observables listed in 'str'
        -O._obs_J 'str'          exclude those QZSS RINEX OBS observables listed in 'str'
        -O._obs_I 'str'          exclude those IRNSS RINEX OBS observables listed in 'str'

     # Options d'edition de RINEX MET :
        -M.r[un_by] 'str'        set RINEX MET header run by to 'str'
        -M.c[omment] 'str'       append RINEX MET header comment 'str'
        -M.mo[nument] 'str'      set RINEX MET header monument name to 'str'
        -M.mn 'str'              set RINEX MET header monument number to 'str'
        -M.obs[_types] 'str'     change RINEX MET header observables to 'str'
                                      'str' = TD+HR+PR sets 3 observables to be TD HR PR, and in that order
        -M._obs[_types] 'str'    exclude those RINEX MET observables listed in 'str'
        -M.mod[el/type/acc] 'obs' 'model' 'type' accuracy  set 'obs' RINEX MET header sensor mod/type/acc to 'model' 'type' accuracy
        -M.pos[ition] 'obs' x y z h  set 'obs' RINEX MET header sensor XYZ/H to x y z h
        -M.dec[imate] #          modulo decimation of MET epochs to # time units
                                      # = 15m results in epochs at 00, 15, 30, and 45 minutes

     # Options d'edition de RINEX NAV :
        -N.s[ystem] #            set RINEX NAV header satellite system to # (= G, R, E, S, C, J or M)
        -N.r[un_by] 'str'        set RINEX NAV header run by to 'str'
        -N.c[omment] 'str'       append RINEX NAV header comment 'str'
        -N.leap #                set RINEX NAV header leap seconds to #

     # Options en mode -conv, pour RINEX OBS V3 seulement :
        -l1_p1                   Privilegie la phase issue du code P1 (si presente) en GPS a celle issue du code C/A sur L1
        -l2_l2c                  Inclut et privilegie la phase issue d'un code Civilian sur L2 (L2C) en GPS (RINEX v2.11)
        -c2_l2c                  Inclut la pseudo-distance issue d'un code Civilian sur L2 (L2C) en GPS (RINEX v2.11)
        -l2c                     Joue le role de -l2_l2c et -c2_l2c (RINEX v2.11)
        -l5                      Inclut les observables issus de la bande L5 en GPS (RINEX v2.11)
        -std                     Joue le role de -l2c et -l5 (RINEX v2.11)
        -l1c                     Inclut les observables Civilian sur L1 (L1C) en GPS (RINEX v2.12)
        -v212                    Joue le role de -l1c, -std et inclut les observables BDS/Compass, QZSS et IRNSS
                                 (RINEX v2.12)
        -rep[ort]                Ecrit un fichier de rapport de la conversion

     # Options en mode -qc :
        -set_mask|masks #        Positionner le masque a # degres
                                 (defaut : 10.00 ; separer par une virgule si plusieurs valeurs)
        -sym[bol_codes]          dump symbol codes and hierarchy for short report qc ASCII timeplot
        -w[idth] #               set time width of qc ASCII timeplot to # (default = 72)
        -lli                     Desactiver l'affichage des indicateurs de Loss Of Lock (symbole L)
     ##############################################################

    """

    #### Convert the paths as Path objects
    out_dir = Path(out_dir)
    ## for RINEX handeling, inp_raw_fpath can ben an iterable (list)
    if utils.is_iterable(inp_raw_fpath):
        raw_fpath_multi = [Path(e) for e in inp_raw_fpath]
        raw_fpath_mono = raw_fpath_multi[0]
    else:  # a single  file, most common case
        raw_fpath_multi = [Path(inp_raw_fpath)]
        raw_fpath_mono = Path(inp_raw_fpath)

    raw_fpath_str_lst = [str(e) for e in raw_fpath_multi]
    out_fpath = out_dir.joinpath(raw_fpath_mono.name + ".rnx_converto")

    cmd_opt_list, _ = _options_list2str(bin_options_custom)
    cmd_kwopt_list, _ = _kw_options_dict2str(bin_kwoptions_custom)

    cmd_list = (
        [bin_path, "-i"]
        + raw_fpath_str_lst
        + ["-o", out_fpath]
        + cmd_opt_list
        + cmd_kwopt_list
    )

    cmd_list = [str(e) for e in cmd_list]
    cmd_str = " ".join(cmd_list)
    cmd_use = [cmd_str]

    return cmd_use, cmd_list, cmd_str


def cmd_build_gfzrnx(
    inp_raw_fpath,
    out_dir,
    bin_options_custom=[],
    bin_kwoptions_custom=dict(),
    bin_path=aro_env_soft_path["gfzrnx"],
):
    """
        Build a command to launch gfzrnx, for RINEX Handeling

        It has the same behavior as all the `cmd_build` functions

        Parameters
        ----------
        inp_raw_fpath : str or Path
            the path of the input Raw GNSS file.
            for RINEX Handeling (e.g. splice) a list of path is allowed.
        out_dir : str or Path
            the path of the output directory.
        bin_options_custom : list, optional
            a list for custom option arguments. The default is [].
        bin_kwoptions_custom : dict, optional
            a dictionary for custom keywords arguments. The default is dict().
        bin_path : str, optional
            the path the executed binary.
            The default is "gfzrnx".

        Returns
        -------
        cmd_use : list of string
            the command as a mono-string in list (singleton).
            Ready to be used by subprocess.run
        cmd_list : list of strings
            the command as a list of strings, splited for each element.
        cmd_str : string
            the command as a concatenated string.

        Warning
        -------
        `gfzrnx` requires a commercial license when used in a **routine environment**

        Note
        ----
        Usage of `gfzrnx`

         file only or common options
         -----------------------------------------------------------------------------------------
         [-h]                      - show this usage message
         [-help]

         [-finp <file list>]       - input  rinex file(s) (std. STDIN).
                                     STDIN is only valid for a single file input.

                                     the following file name types are supported to derive the
                                     nominal epoch/duration information.

                                     RINEX-2 file naming

                                     ssssDDD0.YYx       - daily      file
                                     ssssDDD[a-x].YYx   - hourly     file
                                     ssssDDD[a-x]mm.YYx - sub-hourly file

                                     RINEX-3/4 file naming

                                     SSSSMRCCC_S_YYYYDDDHHMM_NNN_FRQ_TT.FMT
                                     SSSSMRCCC_S_YYYYDDDHHMM_NNN_TT.FMT

                                     see Documentation for details

                                     splice mode:
                                     ------------
                                     * list of input files

         [-fout <file>]            - output rinex or statistics file (std. STDOUT)
                                     automatic output file name if filename given is "::RX2::", "::RX3::" or "::RX4::"

         [-4to9 <file>]            - renaming information for rinex-3 type (re)naming
                                     ( NNNN -> NNNNMRCCC / POTS -> POTS00DEU )

         [-f]                      - force overwrite of output file if it already exists
                                     (std. no overwrite)

         [-sifl]                   - perform an operation on a single file if a file list is
         [-single_file]              provided via "-finp"

         [-ant_rename]             - rename historical antenna names to be IGS conform

      [-nomren23 <[s,][mr,][iso]>] - fast nominal output file name for RINEX-2 to RINEX-3 file renaming.
                                     RINEX-3 output file name is written to STDOUT.

                                        s   - data src (S|R)        (default R)
                                        mr  - marker receiver number   (default 00)
                                        iso - 3 char. iso country code (default XXX)

                                     the input parameters can be given in any order.
                                     supported input file names nnnnddde.yyt[.cmp] or nnnndddedd.yyt[.cmp]

                                     if providing a compressed file all information which is usually taken
                                     from file header (sat. system(s), data frequency) has to be given via the
                                     command line parameter (see documion for details).

         [-vo <2|3|4>]             - output RINEX version (std. latest)
         [--version_out <2|3|4>]
         [-vosc <2|3|4>]           - output RINEX version (fully standard conform)

         [-vnum m.nn]              - change header VERSION number and set output RINEX version
                                     (only the version number is changed / output RINEX version is the highest supported
                                     one)

         [-pr3rx2 <list>]          - komma separated list of list of signal priorities used for rinex 3 -> 2 conversion
                                     to overwrite the standard settings, see documentation for details.

                                     S:n[n...]:STRING

                                     S      - satellite System [CEGJRSI]
                                     n      - frequency number(s)
                                     STRING - prority STRING

                                     G:12:PWCSLXYN,G:5:QXI,R:12:CP

         [-errlog <file>]          - store (append) error logs to a file (std. print to STDERR)

         [-smp <num>]              - sampling rate in sec. (std. no sampling / resolution 1 ms)

         [-smp_nom <num>]          - sampling rate (num) in sec to be used for automatic file naming

         [-smp_lli_shift]          - perform LLI shifts via data sampling to sampling epoch

         [-nav_mixed]              - create a mixed nav. filename

         [-no_nav_stk]             - no nav. splice header statistic tables

         [-stk_obs]                - output data statistics information (std. STDOUT)
         [-stk_only]

         [-crux <file>]            - rinex header manipulations definitions for input files

         [-cx_updins <string(s)>]  - rinex header manipulation(s) definition for input files
                                     given via command line

         [-cx_addinthd]            - if using using a crux-file (-crux) internal/data headers are created
                                     at crux-settings starting epochs.

         [-show_crux]              - show crux structure adopted and used by the program

         [-hded]                   - perform the header edit ONLY mode (with -crux)

         [-stk_epo <n[:list]>]     - ASCII timeplot of data availability (std. STDOUT)
                                     n    - time resolution in seconds
                                     list - comma separated list (prn,otp) (std. prn)

         [-ot <list>]              - obs. types list to be used (pattern matching). the list can be given
         [--obs_types <list>]        globaly or sat. system dependent. the sat. system dependent record
                                     replaces fully a global one.

                                     list can be: [S:]OT1,OT2,...[+S:OT3,OT4,...][+...]

                                     S  - satellite system [CEGJRSI]
                                     OT - observation type identifier

                                     L1,L2,C1,C2,P1,P2
                                     L1,L2,C1,C2,P1,P2+C:L1,L7,C1,C7+G:L1C,L2W,C1,C2

         [-ots <string>[:<attr>]]  - obs. types output sorting
    [--obs_types_sort <string>[:<attr>]]
                                     the "string" consists of the 1st obs. type id. characters ( e.g. CPLDS ),
                                     the "attr" can be [frqasc|frqdsc|frqi,j,...] (frequ. numbers (i,j,...) = 1,...,n),
                                     which means a preferred sorting by frequency (ascending,descending or
                                     a list of distinct frequency numbers)

         [-prn <prn-list>]         - komma separated list of PRNs to be used
                                     range notations are possible G1-32,C01-5,R01-10,E14,E18

         [-no_prn <prn-list>]      - komma separated list of PRNs to be skipped
                                     range notations are possible G1-32,C01-5,R01-10,E14,E18

         [-kaot]                   - keep all obs. types (including fully empty ones)

         [-rsot <n>]               - remove sparse obs. types.
    [--remove_sparse_obs_types <n>]  n - defines the % limit of the median number of observations
                                         per observation type used to delete an observation type fully.

         [-satsys <letters>]       - satellite system(s) to be used (CEGIJRS) (std. CEGIJRS)
                                     C - Beidou
                                     E - Galileo
                                     G - GPS
                                     I - IRNSS
                                     J - QZSS
                                     R - Glonass
                                     S - SBAS

         [-ns        <type>]       - output order of navigation records.   type = [time|prn] (std. prn)
         [--nav_sort <type>]         time - sort by time,prn
                                     prn  - sort by prn,time

         [-nt       <type-list>]   - '+' separated list of nav. selection records (version >= 4).
         [-nav_type <type-list>]     record = [<sat.system(s)>::]<nav.type(s)>:[<message.type(s)]
                                     type(s) are separated via '.'

         [-split n]                - split input file in <n seconds> pieces
                                     - valid only with -fout ::RX2:: or ::RX3::
                                     - valid if n is a multiple of 60 seconds.
                                     - only supported for single input file

         [-chk]                    - extended formal checks on input file (slower)

         [-meta <type[:format]>]   - extract file meta data. the type can be (basic|full).
                                     supported formats are json|xml|txt|dump

         [-fdiff]                  - compare two rinex files of the same format (major version id.)
                                     the two input files have to be given via -finp

         [-met_nwm]                - edit a rinex meteo file(1) by the means of a reference NWM file(2).
                                     the two input files have to be given via -finp.
                                     the second file contains reference NWM data and check limits
                                     (can be used in conjunction with -obs_types, -ot)

         [-site <sitename>]        - use the 4- or 9-char sitename for output filename via automatic file naming
                                     or for header editing settings extractions (crux)
                                     or for "MARKER NAME" in case it is missing.

         [-kv]                     - keep major output version number same as in input

         [-q]                      - quiet mode

         [-d <sec>]                - file duration (seconds) (std. ignored on input
         [--duration <sec>]                                   std. 86400   on output )

         [-epo_beg <EPOCH>]        - first output epoch (<EPOCH> see below)

         [-sei <in|out>]
    [--strict_epoch_interval <in|out>] - output epoch interval according to in/output file name
                                         (only valid in case of RINEX conform file names)

         [-enb <n>]                - extend the nav. epoch interval by +- n seconds
                                     (when using strict epoch interval)

         [-nav_epo_filter]         - only standard epochs are passed to the output
         [-nav_epo_strict]         - only nominal  epochs are passed to the output
         [-nav_latest]             - only latest nav. record per PRN are passed to the output

         [splice_direct]           - use no RAM to store observations via splice operations
                                     (no header data statistics)

         [try_append <sec>]        - try append mode to fasten the splice process with
                                     smallest nominal file duration (seconds) of part files

         [-use_obs_map <file>]     - use modified obs. types mapping
         [-out_obs_map]            - output std.  obs. types mapping

         [-tab]                    - create a tabular data representation output

         [-tab_date]               - use other date (pattern) for tabular observation output
                                     (yyyy-mm-dd|yy-mm-dd|yyyy-ddd|wwww-d|yyyymmdd|yymmdd|yyyyddd|wwwwd|mjd|ddd)

         [-tab_time]               - use other time pattern for tabular observation output
                                     (hh:mm:ss|hhmmss|sod|fod)

         [-tab_sep <string>]       - column separator string (default: BLANK)

         epoch <EPOCH> parameter
         -----------------------------------------------------------------------------------------
         mjd             56753   or        56753_123000
         wwwwd           17870   or        17870_12:30:00
         yyyyddd       2014096   or      2014096_123000
         yyyymmdd     20140406   or     20140406_12:30:00
         yyyy-mm-dd 2014-04-06   or   2014-04-06_123000

         all these date types can be combined via '_' with a time string of type:
         hhmmss
         hh:mm:ss
    """

    #### Convert the paths as Path objects
    out_dir = Path(out_dir)
    ## for RINEX handeling, inp_raw_fpath can ben an iterable (list)
    if utils.is_iterable(inp_raw_fpath):
        raw_fpath_multi = [Path(e) for e in inp_raw_fpath]
        raw_fpath_mono = raw_fpath_multi[0]
    else:  # a single  file, most common case
        raw_fpath_multi = [Path(inp_raw_fpath)]
        raw_fpath_mono = Path(inp_raw_fpath)

    raw_fpath_str_lst = [str(e) for e in raw_fpath_multi]
    out_fpath = out_dir.joinpath(raw_fpath_mono.name + ".rnx_gfzrnx")

    cmd_opt_list, _ = _options_list2str(bin_options_custom)
    cmd_kwopt_list, _ = _kw_options_dict2str(bin_kwoptions_custom)

    cmd_list = (
        [bin_path, "-finp"]
        + raw_fpath_str_lst
        + ["-fout", out_fpath]
        + cmd_opt_list
        + cmd_kwopt_list
    )
    cmd_list = [str(e) for e in cmd_list]
    cmd_str = " ".join(cmd_list)
    cmd_use = [cmd_str]

    return cmd_use, cmd_list, cmd_str
