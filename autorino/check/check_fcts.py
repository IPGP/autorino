#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 27/01/2025 18:53:22

@author: psakic
"""

import termcolor
import pandas as pd


def color(val):
    """
    This function returns a color according to the value of the input.

    Parameters
    ----------
    val: float
        The value to be colored.

    Returns
    -------
    str: color
    """
    if val >= 99.0:
        return "cyan"
    elif val <= 1.0:
        return "red"
    else:
        return "yellow"


def colorize_list(list_inp):
    """
    This function colors the elements of a list according to the value of the element.

    Parameters
    ----------
    list_inp

    Returns
    -------
    list
    """
    return [termcolor.colored(str(e), color(e)) for e in list_inp]


def get_tabult_raw(chk_tab):
    """
    This function returns a check table in tabulate format and a pandas DataFrame
    from the CheckGnss table.

    Parameters
    ----------
    chk_tab : pd.DataFrame
        The table of CheckGnss.

    Returns
    -------
    t_l_str_col_stk : list
        The table in tabulate-ready list of string.
    t_l_str_bnw_stk : list
        The table in tabulate-ready list of string without colors.
    df_chk : pd.DataFrame
        The table in DataFrame format.
    """
    chk_tab = chk_tab.sort_values(["epoch_srt", "site"])
    sites = chk_tab["site"].unique()
    t_l_str_col_stk = [["epoch_srt"] + list(sites)]
    t_l_str_bnw_stk = [["epoch_srt"] + list(sites)]
    t_l_flt_stk = []

    for epo, chk_epo in reversed(list(chk_tab.groupby("epoch_srt"))):
        epo = pd.Timestamp(epo)
        l_flt = [epo] + list(chk_epo["%"].tolist())
        l_str_col = [epo.strftime("%Y-%j %H:%M")] + colorize_list(chk_epo["%"].tolist())
        l_str_bnw = [epo.strftime("%Y-%j %H:%M")] + chk_epo["%"].tolist()
        t_l_str_col_stk.append(l_str_col)
        t_l_str_bnw_stk.append(l_str_bnw)
        t_l_flt_stk.append(l_flt)

    df_chk = pd.DataFrame(t_l_flt_stk, columns=t_l_str_col_stk[0])
    df_chk.set_index("epoch_srt", inplace=True)

    return t_l_str_col_stk, t_l_str_bnw_stk, df_chk
