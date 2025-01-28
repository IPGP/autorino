#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 27/01/2025 09:50:23

@author: psakic
"""

import autorino.check as arochk
import autorino.common as arocmn
import timeit
import pandas as pd
import os
import tabulate

def check_rnx(inp_dir_parent,
              inp_dir_structure,
              epoch_start,
              epoch_end,
              print_check_tabulate=False,
              sites_list=[]):

    inp_dir = os.path.join(inp_dir_parent, inp_dir_structure)

    if sites_list:
        sites_use = sites_list
    else:
        sites_use = arocmn.guess_sites_list(inp_dir_parent)

    chk_stk = []
    for site in sites_use:
        eporng = arocmn.EpochRange(epoch_start,
                                   epoch_end)
        chk = arochk.CheckGnss(inp_dir=str(inp_dir),
                                site={'site_id': site},
                                epoch_range=eporng)
        chk.site_id = site
        chk.check()
        chk_stk.append(chk)

    chk_table_cat = pd.concat([c.table for c in chk_stk])

    t_l_str_stk, df_chk = arochk.get_tabult_raw(chk_table_cat)
    tabu_chk = tabulate.tabulate(t_l_str_stk,
                                 headers="firstrow",
                                 tablefmt="fancy_grid")
    if print_check_tabulate:
        print(tabu_chk)

    return tabu_chk, df_chk

dir_parent = "/home/psakicki/aaa_FOURBI/OVSM/"
dir_struct = "%Y/%j/rinex"
tabu_chk0, df_chk0 = check_rnx(dir_parent, dir_struct,
                               "2025-01-01", "2025-01-15",
                               print_check_tabulate=True)

df_chk0.plot(marker='.')
