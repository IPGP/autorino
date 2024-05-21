#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 25 19:20:22 2024

@author: psakic
"""

import os
import re

from geodezyx import utils


##### Frontend function

def translator(path_inp, translator_dict=None, epoch_inp=None):
    """
    Translates a given path using environment variables, epoch information, and a provided dictionary.

    Parameters
    ----------
    path_inp : str
        The input path to be translated.
    translator_dict : dict, optional
        A dictionary containing keywords and their corresponding values for translation. Default is None.
    epoch_inp : datetime, optional
        A datetime object containing epoch information for translation. Default is None.

    Returns
    -------
    str
        The translated path.

    Notes
    -----
    The function first translates any environment variables in the path. If epoch information is provided, it is used
    to translate any strftime aliases in the path. If a translator dictionary is provided, it is used to translate
    any keywords in the path.
    """

    path_translated = str(path_inp)
    path_translated = _translator_env_variables(path_translated)
    if epoch_inp:
        path_translated = _translator_epoch(path_translated, epoch_inp)
    if translator_dict:
        path_translated = _translator_keywords(path_translated, translator_dict)
    return path_translated

##### Internal functions


def _translator_epoch(path_inp, epoch_inp):
    """
    Translates strftime aliases in the input path using the provided epoch information.

    This function is used internally by the translator function to handle strftime aliases in the path.
    It also handles the special aliases <HOURCHAR> and <hourchar>, which are replaced with the hour of the epoch
    in uppercase and lowercase letters, respectively.

    Parameters
    ----------
    path_inp : str
        The input path containing strftime aliases to be translated.
    epoch_inp : datetime
        A datetime object containing the epoch information used for translation.

    Returns
    -------
    str
        The translated path with strftime aliases replaced with the corresponding epoch information.

    Notes
    -----
    For more information on strftime and strptime behavior, see:
    https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior
    """
    path_translated = str(path_inp)
    path_translated = epoch_inp.strftime(path_translated)

    # the <HOURCHAR> and <hourchar> alias in a time information,
    # thus must be managed here
    ichar = epoch_inp.hour
    path_translated = path_translated.replace('<HOURCHAR>', utils.alphabet(ichar).upper())
    path_translated = path_translated.replace('<hourchar>', utils.alphabet(ichar).lower())

    return path_translated

def _translator_keywords(path_inp, translator_dict):
    """
    Translates keywords in the input path using the provided dictionary.

    This function is used internally by the translator function to handle keywords in the path.
    It replaces each keyword enclosed in angle brackets (e.g., <keyword>) with its corresponding value from the dictionary.
    Keywords are case-sensitive and must not be prefixed with a dollar sign ($).

    Parameters
    ----------
    path_inp : str
        The input path containing keywords to be translated.
    translator_dict : dict
        A dictionary containing keywords and their corresponding values for translation.

    Returns
    -------
    str
        The translated path with keywords replaced with their corresponding values from the dictionary.

    Notes
    -----
    If a keyword in the path does not exist in the dictionary, it will remain unchanged in the translated path.
    """
    path_translated = str(path_inp)

    # replace autorino variable (without a <$....>)
    if re.search('<(?!.*\$).*>', path_translated):
        for k, v in translator_dict.items():
            path_translated = path_translated.replace("<"+k+">", str(v))

    return path_translated

def _translator_env_variables(path_inp):
    """
    Translates environment variables in the input path.

    This function is used internally by the translator function to handle environment variables in the path.
    It replaces each environment variable enclosed in angle brackets and prefixed with a dollar sign (e.g., <$VAR>)
    with its corresponding value from the system's environment variables.

    Parameters
    ----------
    path_inp : str
        The input path containing environment variables to be translated.

    Returns
    -------
    str
        The translated path with environment variables replaced with their corresponding values from the system's environment variables.

    Notes
    -----
    If an environment variable in the path does not exist in the system's environment variables, it will remain unchanged in the translated path.
    """
    path_translated = str(path_inp)

    # replace system environment variables
    if re.search('<\$.*>', path_translated):
        for k, v in os.environ.items():
            path_translated = path_translated.replace("<$"+k+">", str(v))

    return path_translated


