#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 17/04/2026

@author: psakic

Utility functions shared across autorino CLI entry-points.
"""

import os


def prep_inputs(inp, list_file_input=False):
    """
    Prepare the list of input files for autorino CLI entry-points.

    Handles three input styles:

    * ``list_file_input=True``: ``inp[0]`` is a text file whose lines are
      the actual file paths → returns a list of strings.
    * Single path that is a directory → returns the directory path as a string.
    * One or several explicit paths → returns them as a list.

    Parameters
    ----------
    inp : list of str
        Raw list of input paths as received from ``argparse`` (``nargs="+"``).
        Typically ``args.rnxs_inp``, ``args.inp_raws``, etc.
    list_file_input : bool, optional
        If ``True``, ``inp[0]`` is treated as a text file containing one file
        path per line. Defaults to ``False``.

    Returns
    -------
    str or list of str
        Either a directory path (str) or a list of file paths.
    """
    if list_file_input:
        # Input is a text file listing the actual paths, one per line
        with open(inp[0], "r") as fh:
            return fh.read().splitlines()
    elif len(inp) == 1 and os.path.isdir(inp[0]):
        # Input is a single directory
        return inp[0]
    else:
        # One or several explicit file paths
        return inp


