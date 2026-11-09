#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Converted files regular expressions functions
"""

import re
from pathlib import Path


# Configuration for each converter's regex patterns
CONVERTER_REGEX_CONFIGS = {
    'void': {
        'main': lambda f: f.name,
        'annex': lambda f: f.name,
    },
    'runpkr00': {
        'main': lambda f: f.with_suffix(".tgd").name,
        'annex': lambda f: f.stem,
    },
    'teqc': {
        'main': lambda f: f.name + ".rnx_teqc",
        'annex': lambda f: f.name + ".rnx_teqc",
    },
    'converto': {
        'main': lambda f: f.name + ".rnx_converto",
        'annex': lambda f: f.name + ".rnx_converto",
    },
    'gfzrnx': {
        'main': lambda f: f.name + ".rnx_gfzrnx",
        'annex': lambda f: f.name + ".rnx_gfzrnx",
    },
    'trm2rinex': {
        'main': lambda f: _get_year_based_regex(f, "o"),
        'annex': lambda f: _get_year_based_regex(f, ""),
    },
    't0xconvert': {
        'main': lambda f: _get_year_based_regex(f, "o"),
        'annex': lambda f: _get_year_based_regex(f, ""),
    },
    'mdb2rnx': {
        'main': lambda f: _get_mdb_regex(f, "o"),
        'annex': lambda f: _get_mdb_regex(f, r"\w"),
    },
    'convbin': {
        'main': lambda f: f.with_suffix(".obs").name,
        'annex': lambda f: f.stem,
    },
    'tps2rin': {
        'main': lambda f: _get_tps_regex(f, "o"),
        'annex': lambda f: _get_tps_regex(f, r"\w"),
    },
}


def conv_regex_generic(f, converter_name):
    """
    Generate regex patterns for converted files based on converter type.

    Parameters
    ----------
    f : str or Path
        Input raw filename or path
    converter_name : str
        Name of the converter (e.g., 'sbf2rin', 'teqc', 'runpkr00')

    Returns
    -------
    conv_regex_main, conv_regex_annex : tuple of compiled regex
        Main regex (observation RINEX) and annex regex (all output files)

    Note
    ----
    Main regex matches the primary observation file.
    Annex regex matches all output files (including main).
    Main is processed before annex, so annex excludes main in practice.
    """
    f = Path(Path(f).name)  # Keep filename only

    if converter_name not in CONVERTER_REGEX_CONFIGS:
        raise ValueError(f"Unknown converter: {converter_name}")

    config = CONVERTER_REGEX_CONFIGS[converter_name]
    main_pattern = config['main'](f)
    annex_pattern = config['annex'](f)

    return re.compile(main_pattern), re.compile(annex_pattern)


def conv_regex_custom(regex_tup_inp):
    """
    Generate regex from custom tuple of regex strings.

    Parameters
    ----------
    regex_tup_inp : tuple of (str, str)
        Regex strings for (main, annex) files

    Returns
    -------
    conv_regex_main, conv_regex_annex : tuple of compiled regex
    """
    regex_main, regex_annex = regex_tup_inp
    return re.compile(regex_main), re.compile(regex_annex)


# Helper functions for complex regex patterns
def _get_year_based_regex(f, suffix):
    """Extract year from filename and build regex (trm2rinex, t0xconvert)."""
    date_full = re.search("20[0-9]{10}", f.name).group()
    yyyy = date_full[:4]
    return f.with_suffix("." + yyyy[2:] + suffix).name if suffix else f.with_suffix("." + yyyy[2:]).name


def _get_mdb_regex(f, suffix):
    """Build regex for mdb2rnx converter."""
    finp = str(f)

    if finp.lower().endswith("mdb"):
        regex_doy_site = r".(\w{4})(-Leica)?.([0-9]{2})([0-9]{3})"
        doygroup = 4
    elif finp.lower().endswith("m00"):
        regex_doy_site = r"(\w{4})([0-9]{3})"
        doygroup = 2
    else:
        regex_doy_site = r"(\w{4})([0-9]{3})"
        doygroup = 2

    site = re.match(regex_doy_site, f.name).group(1).lower()
    doy = re.match(regex_doy_site, f.name).group(doygroup).lower()
    return site + doy + r".(.{2})?\.[0-9]{2}" + suffix


def _get_tps_regex(f, suffix):
    """Build regex for tps2rin converter."""
    regex_site = r"^(\w{4})"
    site = re.match(regex_site, f.name).group(1).lower()
    return site + r"[0-9]{3}.(.|)\.[0-9]{2}" + suffix


# Backward-compatible wrapper functions
def conv_regex_void(f):
    return conv_regex_generic(f, 'void')

def conv_regex_runpkr00(f):
    return conv_regex_generic(f, 'runpkr00')

def conv_regex_teqc(f):
    return conv_regex_generic(f, 'teqc')

def conv_regex_converto(f):
    return conv_regex_generic(f, 'converto')

def conv_regex_gfzrnx(f):
    return conv_regex_generic(f, 'gfzrnx')

def conv_regex_trm2rinex(f):
    return conv_regex_generic(f, 'trm2rinex')

def conv_regex_t0xconvert(f):
    return conv_regex_generic(f, 't0xconvert')

def conv_regex_mdb2rnx(f):
    return conv_regex_generic(f, 'mdb2rnx')

def conv_regex_convbin(f):
    return conv_regex_generic(f, 'convbin')

def conv_regex_tps2rin(f):
    return conv_regex_generic(f, 'tps2rin')
