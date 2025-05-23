#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 29 11:53:09 2024

@author: psakic

This module, decompress.py, provides functions for decompressing files,
specifically those that are gzipped or in Hatanaka-compressed RINEX format.
"""

import gzip

import os
import shutil
from pathlib import Path

import hatanaka

from geodezyx import conv

#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger("autorino")
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])


def is_compressed(file_inp):
    """
    Checks if a file is compressed based on its extension.

    Parameters
    ----------
    file_inp : str
        The input file to check.

    Returns
    -------
    bool
        True if the file is compressed, False otherwise.
    """
    file_inp2 = Path(file_inp)

    ext = file_inp2.suffix.lower()

    if ext in (".gz",):
        bool_compress = True
    else:
        bool_compress = False

    return bool_compress


def decomp_gzip(gzip_file_inp, out_dir_inp=None, force=False):
    """
    Decompresses a gzipped file.

    Parameters
    ----------
    gzip_file_inp : str
        The input gzipped file to decompress.
    out_dir_inp : str, optional
        The output directory where the decompressed file will be stored.
        If not provided, the decompressed file will be stored in the same directory as the input file.
    force : bool, optional
        If True, the file will be decompressed even if a decompressed file already exists.

    Returns
    -------
    str
        The path to the decompressed file.
    """
    gzip_file_inp = str(gzip_file_inp)
    gzip_file2 = Path(gzip_file_inp)

    if not out_dir_inp:
        out_dir = gzip_file2.parent
    else:
        out_dir = Path(out_dir_inp)

    file_out = out_dir.joinpath(gzip_file2.stem)

    if file_out.exists() and not force:
        pass
    else:
        with gzip.open(gzip_file_inp, "rb") as f_in:
            with open(file_out, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        logger.debug("decompress (gzip): %s > %s", gzip_file2.name, file_out)

    return str(file_out)


def decomp_hatanaka(crx_file_inp, out_dir_inp=None, force=False):
    """
    Decompresses a Hatanaka-compressed RINEX file.

    Parameters
    ----------
    crx_file_inp : str
        The input Hatanaka-compressed RINEX file to decompress.
    out_dir_inp : str, optional
        The output directory where the decompressed file will be stored.
        If not provided, the decompressed file will be stored in the same directory as the input file.
    force : bool, optional
        If True, the file will be decompressed even if a decompressed file already exists.

    Returns
    -------
    str
        The path to the decompressed file.
    """
    crx_file_inp = str(crx_file_inp)
    crx_file_inp2 = Path(crx_file_inp)

    if out_dir_inp:
        out_dir = out_dir_inp
        crx_file = shutil.copy2(crx_file_inp, out_dir)
        dell = True
    else:
        out_dir = os.path.dirname(crx_file_inp)
        crx_file = crx_file_inp
        dell = False

    rnx_name_potential = os.path.basename(crx_file).split(".")[0] + ".rnx"
    rnx_file_potential = os.path.join(out_dir, rnx_name_potential)

    if os.path.isfile(rnx_file_potential) and not force:
        rnx_file_out = rnx_file_potential
    else:
        rnx_file_out = hatanaka.decompress_on_disk(crx_file, delete=dell)
        logger.debug("decompress (hatanaka): %s > %s", crx_file_inp2.name, rnx_file_out)

    return str(rnx_file_out)


def decompress_file(file_inp, out_dir_inp=None, force=False):
    """
    Decompresses a file. The file can be gzipped or in Hatanaka-compressed RINEX format.

    Parameters
    ----------
    file_inp : str
        The input file to decompress.
    out_dir_inp : str, optional
        The output directory where the decompressed file will be stored.
        If not provided, the decompressed file will be stored in the same directory as the input file.
    force : bool, optional
        If True, the file will be decompressed even if a decompressed file already exists.

    Returns
    -------
    str
        The path to the decompressed file.
    bool
        True if the file was decompressed, False otherwise.
    """
    file_inp = str(file_inp)
    file_inp2 = Path(file_inp)
    ext = file_inp2.suffix.lower()

    if not os.path.isfile(file_inp):
        logger.warning("unable to decompress, file not exists: %s", file_inp2.name)
        file_out = file_inp
        bool_decomp_out = False
    ## RINEX Case
    elif conv.rinex_regex_search_tester(file_inp, compressed=True):
        file_out = decomp_hatanaka(file_inp, out_dir_inp, force=force)
        bool_decomp_out = True
    ## Generic gzipped case (e.g. RAW file)
    elif ext == ".gz":
        file_out = decomp_gzip(file_inp, out_dir_inp, force=force)
        bool_decomp_out = True
    else:
        logger.debug("no valid compression for %s, nothing is done", file_inp2.name)
        file_out = file_inp
        bool_decomp_out = False

    return file_out, bool_decomp_out
