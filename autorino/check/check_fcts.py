#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 27/01/2025 18:53:22

@author: psakic
"""

import termcolor
import pandas as pd
import tabulate


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
    return [termcolor.colored(str(e), color(e)) for e in list_inp]


def get_tabult_raw(chk_tab, short_label=False):
    chk_tab = chk_tab.sort_values(["epoch_srt", "site"])
    sites = list(chk_tab["site"].unique())

    if short_label
        print(sites)
        sites = [s[:4] for s in sites]
        fmt_time = "%Y-%j"
    else:
        fmt_time = "%Y-%j %H:%M"

    tab_chk_raw_col = [["epoch_srt"] + sites]
    tab_chk_raw_bnw = [["epoch_srt"] + sites]
    flt_data_stk = []

    for epo, chk_epo in reversed(list(chk_tab.groupby("epoch_srt"))):
        epo = pd.Timestamp(epo)
        l_flt = [epo] + list(chk_epo["%"].tolist())
        l_str_col = [epo.strftime(fmt_time)] + list(colorize_list(chk_epo["%"].tolist()))
        l_str_bnw = [epo.strftime(fmt_time)] + chk_epo["%"].tolist()
        flt_data_stk.append(l_flt)
        tab_chk_raw_col.append(l_str_col)
        tab_chk_raw_bnw.append(l_str_bnw)


    tabu_chk_col = tabulate.tabulate(tab_chk_raw_col,
                                     headers="firstrow",
                                     tablefmt="grid")
    tabu_chk_bnw = tabulate.tabulate(tab_chk_raw_bnw,
                                    headers="firstrow",
                                    tablefmt="grid")

    df_chk_sum = pd.DataFrame(flt_data_stk, columns=tab_chk_raw_col[0])
    df_chk_sum.set_index("epoch_srt", inplace=True)

    return tabu_chk_col, tabu_chk_bnw, df_chk_sum
