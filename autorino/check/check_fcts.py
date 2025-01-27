#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 27/01/2025 18:53:22

@author: psakic
"""

import termcolor

def color(val):
    if val >= 99.:
        return "cyan"
    elif val <= 1.:
        return "red"
    else:
        return "yellow"

def colorize_list(list_inp):
    return [termcolor.colored(str(e), color(e)) for e in list_inp]


def tabulate_check(chk_tab):
    chk_tab = chk_tab.sort_values(["epoch_srt","site_id"])
    sites = chk_tab["site_id"].unique()
    tab_lines_stk = [['dates'] + list(sites)]
    for epo, chk_epo in chk_tab.groupby("epoch_srt"):
        epo = pd.Timestamp(epo)
        l = [ epo.strftime("%Y-%j %H:%M") ] + arochk.colorize_list(chk_epo["%"].tolist())
        tab_lines_stk.append(l)
    return tab_lines_stk


