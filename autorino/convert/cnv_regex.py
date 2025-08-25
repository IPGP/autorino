#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 14 12:03:40 2023

@author: psakic

#### converted files regular expressions functions
#### main = the regex for the main file i.e. the Observation RINEX
#### annex = the regex for the ALL outputed files (Observation RINEX included)
#### the main with be processed before the annex,
#### thus annex regex will finally not include the main
"""

import re
from pathlib import Path


###################################################################


def conv_regex_void(f):
    """
    Generate the regular expressions of the main and annex converted files
    equivalent to the input filename

    ** Must be used for test purposes only !**

    It has the same behavior as all the `conv_regex` functions
    See note below

    Parameters
    ----------
    f : str or Path
        the input Raw filename or path
        (the filename will be extracted in the function).

    Returns
    -------
    conv_regex_main & conv_regex_annex : Complied Regex Objects
        The regular expressions.

    Note
    ----
    general behavior of the `conv_regex` functions:
    main = the regex for the main file i.e. the Observation RINEX
    annex = the regex for the ALL outputed files (Observation RINEX included)
    the main with be processed before the annex,
    thus annex regex will finally not include the main one
    """

    f = Path(Path(f).name)  ### keep the filename only
    conv_regex_main = re.compile(f.name)
    conv_regex_annex = re.compile(f.name)
    return conv_regex_main, conv_regex_annex


def conv_regex_custom(regex_tup_inp):
    """
    Generate the regular expressions of the main and annex converted files
    equivalent to the input regex tuple

    It has the same behavior as all the `conv_regex` functions
    See note below
    **but** the input is a tuple of regex strings
    not the input raw filename

    Parameters
    ----------
    regex_tup_inp : 2-tuple of str
        the input tuple of 2 regex strings for main and annex files

    Returns
    -------
    conv_regex_main & conv_regex_annex : Complied Regex Objects
        The regular expressions.

    Note
    ----
    general behavior of the `conv_regex` functions:
    main = the regex for the main file i.e. the Observation RINEX
    annex = the regex for the ALL outputed files (Observation RINEX included)
    the main with be processed before the annex,
    thus annex regex will finally not include the main one

    """
    regex_main, regex_annex = regex_tup_inp
    conv_regex_main = re.compile(regex_main)
    conv_regex_annex = re.compile(regex_annex)
    return conv_regex_main, conv_regex_annex


def conv_regex_runpkr00(f):
    """
    Generate the regular expressions of the mainand annex converted files
    outputed by runpkr00 (Trimble)

    It has the same behavior as all the `conv_regex` functions
    See note below

    Parameters
    ----------
    f : str or Path
        the input Raw filename or path
        (the filename will be extracted in the function).

    Returns
    -------
    conv_regex_main & conv_regex_annex : Complied Regex Objects
        The regular expressions.

    Note
    ----
    general behavior of the `conv_regex` functions:
    main = the regex for the main file i.e. the Observation RINEX
    annex = the regex for the ALL outputed files (Observation RINEX included)
    the main with be processed before the annex,
    thus annex regex will finally not include the main one
    """

    # PSA1______202110270000A.tgd (option -d -g)
    # PSA1______202110270000A.tg! (opened/working file)
    # ABD0______202110270000A.dat (when not option -g in runpkr)
    f = Path(Path(f).name)  ### keep the filename only
    conv_regex_main = re.compile(f.with_suffix(".tgd").name)
    conv_regex_annex = re.compile(f.stem)
    return conv_regex_main, conv_regex_annex


def conv_regex_teqc(f):
    """
    Generate the regular expressions of the main and annex converted files
    outputed by teqc (polyvalent)

    It has the same behavior as all the `conv_regex` functions
    See note below

    Parameters
    ----------
    f : str or Path
        the input Raw filename or path
        (the filename will be extracted in the function).

    Returns
    -------
    conv_regex_main & conv_regex_annex : Complied Regex Objects
        The regular expressions.

    Note
    ----
    general behavior of the `conv_regex` functions:
    main = the regex for the main file i.e. the Observation RINEX
    annex = the regex for the ALL outputed files (Observation RINEX included)
    the main with be processed before the annex,
    thus annex regex will finally not include the main one
    """
    f = Path(Path(f).name)  ### keep the filename only
    # conv_regex_main = re.compile(f.with_suffix(".rnx_teqc").name)
    conv_regex_main = re.compile(f.name + ".rnx_teqc")
    conv_regex_annex = conv_regex_main
    return conv_regex_main, conv_regex_annex


def conv_regex_converto(f):
    """
    Generate the regular expressions of the main and annex converted files
    outputed by converto (polyvalent)

    It has the same behavior as all the `conv_regex` functions
    See note below

    Parameters
    ----------
    f : str or Path
        the input Raw filename or path
        (the filename will be extracted in the function).

    Returns
    -------
    conv_regex_main & conv_regex_annex : Complied Regex Objects
        The regular expressions.

    Note
    ----
    general behavior of the `conv_regex` functions:
    main = the regex for the main file i.e. the Observation RINEX
    annex = the regex for the ALL outputed files (Observation RINEX included)
    the main with be processed before the annex,
    thus annex regex will finally not include the main one
    """
    f = Path(Path(f).name)  ### keep the filename only
    # conv_regex_main = re.compile(f.with_suffix(".rnx_teqc").name)
    conv_regex_main = re.compile(f.name + ".rnx_converto")
    conv_regex_annex = conv_regex_main
    return conv_regex_main, conv_regex_annex


def conv_regex_gfzrnx(f):
    """
    Generate the regular expressions of the main and annex converted files
    outputed by GFZRNX (polyvalent)

    It has the same behavior as all the `conv_regex` functions
    See note below

    Parameters
    ----------
    f : str or Path
        the input Raw filename or path
        (the filename will be extracted in the function).

    Returns
    -------
    conv_regex_main & conv_regex_annex : Complied Regex Objects
        The regular expressions.

    Note
    ----
    general behavior of the `conv_regex` functions:
    main = the regex for the main file i.e. the Observation RINEX
    annex = the regex for the ALL outputed files (Observation RINEX included)
    the main with be processed before the annex,
    thus annex regex will finally not include the main one
    """
    f = Path(Path(f).name)  ### keep the filename only
    # conv_regex_main = re.compile(f.with_suffix(".rnx_teqc").name)
    conv_regex_main = re.compile(f.name + ".rnx_gfzrnx")
    conv_regex_annex = conv_regex_main
    return conv_regex_main, conv_regex_annex


def conv_regex_trm2rinex(f):
    """
    Generate the regular expressions of the mainand annex converted files
    outputed by trm2rinex (Trimble)

    It has the same behavior as all the `conv_regex` functions
    See note below

    Parameters
    ----------
    f : str or Path
        the input Raw filename or path
        (the filename will be extracted in the function).

    Returns
    -------
    conv_regex_main & conv_regex_annex : Complied Regex Objects
        The regular expressions.

    Note
    ----
    general behavior of the `conv_regex` functions:
    main = the regex for the main file i.e. the Observation RINEX
    annex = the regex for the ALL outputed files (Observation RINEX included)
    the main with be processed before the annex,
    thus annex regex will finally not include the main one
    """

    # "/home/psakicki/aaa_FOURBI/convertertest/AGAL______202110270000A.21o",
    # "/home/psakicki/aaa_FOURBI/convertertest/AGAL______202110270000A.21l",
    # "/home/psakicki/aaa_FOURBI/convertertest/AGAL______202110270000A.21g",
    # "/home/psakicki/aaa_FOURBI/convertertest/AGAL______202110270000A.21n"
    f = Path(Path(f).name)  ### keep the filename only
    # date_full = re.search("[0-9]{12}[a-zA-Z]",f.name).group() ##too restrictive, sometime there is no final letter
    date_full = re.search("20[0-9]{10}", f.name).group()
    yyyy = date_full[:4]
    conv_regex_main = re.compile(f.with_suffix("." + yyyy[2:] + "o").name)
    conv_regex_annex = re.compile(f.with_suffix("." + yyyy[2:]).name)
    return conv_regex_main, conv_regex_annex


def conv_regex_t0xconvert(f):
    """
    Generate the regular expressions of the mainand annex converted files
    outputed by t0xconvert (Trimble)

    It has the same behavior as all the `conv_regex` functions
    See note below

    Parameters
    ----------
    f : str or Path
        the input Raw filename or path
        (the filename will be extracted in the function).

    Returns
    -------
    conv_regex_main & conv_regex_annex : Complied Regex Objects
        The regular expressions.

    Note
    ----
    general behavior of the `conv_regex` functions:
    main = the regex for the main file i.e. the Observation RINEX
    annex = the regex for the ALL outputed files (Observation RINEX included)
    the main with be processed before the annex,
    thus annex regex will finally not include the main one
    """

    f = Path(Path(f).name)  ### keep the filename only
    # date_full = re.search("[0-9]{12}[a-zA-Z]",f.name).group() ##too restrictive, sometime there is no final letter
    date_full = re.search("20[0-9]{10}", f.name).group()
    yyyy = date_full[:4]
    conv_regex_main = re.compile(f.with_suffix("." + yyyy[2:] + "o").name)
    conv_regex_annex = re.compile(f.with_suffix("." + yyyy[2:]).name)
    return conv_regex_main, conv_regex_annex


def conv_regex_mdb2rnx(f):
    """
    Generate the regular expressions of the mainand annex converted files
    outputed by mdb2rnx (Leica)

    It has the same behavior as all the `conv_regex` functions
    See note below

    Parameters
    ----------
    f : str or Path
        the input Raw filename or path
        (the filename will be extracted in the function).

    Returns
    -------
    conv_regex_main & conv_regex_annex : Complied Regex Objects
        The regular expressions.

    Note
    ----
    general behavior of the `conv_regex` functions:
    main = the regex for the main file i.e. the Observation RINEX
    annex = the regex for the ALL outputed files (Observation RINEX included)
    the main with be processed before the annex,
    thus annex regex will finally not include the main one
    """

    # souf3000.21o
    # souf3000.21n
    # souf3000.21l
    # souf3000.21g
    ### met also for OVSM
    # fsdc176p11.18o
    # mlm0236a00.18n
    # mlm0236a00.18l
    # mlm0236a00.18g
    # fsdc176p11.18o
    # fsdc176p11.18n
    # fsdc176p11.18g
    # and even for OVSG
    # souf226n 8.24l
    # souf226n 8.24n
    # souf226n 8.24o

    finp = str(f)
    f = Path(Path(f).name)  ### keep the filename only
    if finp.lower().endswith("mdb"):
        # used in OVSM e.g.
        # LAJB0a18002.MDB
        # LMLM0-Leicaa18233.MDB
        regex_doy_site = r".(\w{4})(-Leica)?.([0-9]{2})([0-9]{3})"
        doygroup = 4
        # alternativelywe can exclude the group 'Leica-' with ?:
        # regex_doy_site=r".(\w{4})(?:-Leica)?.([0-9]{2})([0-9]{3})"
        # doygroup = 3
    elif finp.lower().endswith("m00"):
        # used in OVSG e.g.
        # PAR1323a.m00
        regex_doy_site = r"(\w{4})([0-9]{3})"
        doygroup = 2
    else:
        regex_doy_site = r"(\w{4})([0-9]{3})"
        doygroup = 2

    site = re.match(regex_doy_site, f.name).group(1).lower()
    doy = re.match(regex_doy_site, f.name).group(doygroup).lower()
    conv_regex_main = re.compile(site + doy + r".(.{2})?\.[0-9]{2}o")
    conv_regex_annex = re.compile(site + doy + r".(.{2})?\.[0-9]{2}\w")
    return conv_regex_main, conv_regex_annex


def conv_regex_convbin(f):
    """
    Generate the regular expressions of the mainand annex converted files
    outputed by RTKLIB's convbin (polyvalent)

    It has the same behavior as all the `conv_regex` functions
    See note below

    Parameters
    ----------
    f : str or Path
        the input Raw filename or path
        (the filename will be extracted in the function).

    Returns
    -------
    conv_regex_main & conv_regex_annex : Complied Regex Objects
        The regular expressions.

    Note
    ----
    general behavior of the `conv_regex` functions:
    main = the regex for the main file i.e. the Observation RINEX
    annex = the regex for the ALL outputed files (Observation RINEX included)
    the main with be processed before the annex,
    thus annex regex will finally not include the main one
    """
    # Input
    # NBIM0a20221226.BNX
    # Output
    # NBIM0a20221226.obs
    # NBIM0a20221226.nav
    # NBIM0a20221226.sbs
    f = Path(Path(f).name)  ### keep the filename only
    conv_regex_main = re.compile(f.with_suffix(".obs").name)
    conv_regex_annex = re.compile(f.stem)
    return conv_regex_main, conv_regex_annex


def conv_regex_tps2rin(f):
    """
    Generate the regular expressions of the main and annex converted files
    outputed by tps2rin (Topcon)

    It has the same behavior as all the `conv_regex` functions
    See note below

    Parameters
    ----------
    f : str or Path
        the input Raw filename or path
        (the filename will be extracted in the function).

    Returns
    -------
    conv_regex_main & conv_regex_annex : Complied Regex Objects
        The regular expressions.

    Note
    ----
    general behavior of the `conv_regex` functions:
    main = the regex for the main file i.e. the Observation RINEX
    annex = the regex for the ALL outputed files (Observation RINEX included)
    the main with be processed before the annex,
    thus annex regex will finally not include the main one
    """
    # Input
    # DHS030011.TPS
    # Output
    # an extra character is added if there is already an existing file
    # dhs030002.11p
    # dhs030002.11p
    # dhs030002.11o
    # dhs030001.11p
    # dhs030001.11o
    # dhs030000.11p
    # dhs030000.11o
    # dhs03000.11p
    # dhs03000.11o

    f = Path(Path(f).name)  ### keep the filename only
    ### this regey_doy_site is too restricitive, it does not work for all tps files
    #regex_doy_site = r"(\w{4})([0-9]{3})"
    #site = re.match(regex_doy_site, f.name).group(1).lower()
    # a less restricitive regex_site
    regex_site = r"^(\w{4})"
    site = re.match(regex_site, f.name).group(1).lower()

    # doy=re.match(regex_doy_site,f.name).group(2).lower()
    # conv_regex_main = re.compile(site+doy+".(.|)\.[0-9]{2}o")
    # conv_regex_annex  = re.compile(site+doy+".(.|)\.[0-9]{2}\w")
    ## the date of the raw file can be actually anything...
    ## doy/month-day/etc..
    conv_regex_main = re.compile(site + r"[0-9]{3}.(.|)\.[0-9]{2}o")
    conv_regex_annex = re.compile(site + r"[0-9]{3}.(.|)\.[0-9]{2}\w")

    return conv_regex_main, conv_regex_annex

