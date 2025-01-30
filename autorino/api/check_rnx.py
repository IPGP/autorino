#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 27/01/2025 09:50:23

@author: psakic
"""
import matplotlib.pyplot as plt

import autorino.cfgenv as aroenv
import autorino.check as arochk
import autorino.common as arocmn
import timeit
import pandas as pd
import os
import tabulate
import logging
from geodezyx import utils

logger = logging.getLogger("autorino")
logger.setLevel(aroenv.aro_env_dict["general"]["log_level"])


def check_rnx(
    inp_dir_parent,
    inp_dir_structure,
    epoch_start,
    epoch_end,
    sites_list=[],
    output_dir=None,
):

    inp_dir = os.path.join(inp_dir_parent, inp_dir_structure)
    eporng = arocmn.EpochRange(epoch_start, epoch_end)

    if sites_list:
        sites_use = sites_list
    else:
        sites_use = arocmn.guess_sites_list(inp_dir_parent)

    chk_tab_stk = []
    chk_tab_stats_stk = []
    for site in sites_use:
        logger.critical(site)
        chk = arochk.CheckGnss(
            inp_dir=str(inp_dir), site={"site_id": site}, epoch_range=eporng
        )
        chk.check()
        chk_tab_stk.append(chk.table)
        chk_tab_stats_stk.append(chk.table_stats)

    df_chk_table_cat = pd.concat(chk_tab_stk)
    df_chk_full_stats = pd.concat(chk_tab_stats_stk)

    tabu_chk_col, tabu_chk_bnw, df_chk_sum = arochk.get_tabult_raw(
        df_chk_table_cat, short_label=True
    )

    logger.info("Check: \n" + tabu_chk_col)

    if output_dir:
        checkrnx_output(
            output_dir,
            eporng,
            tabu_chk_col,
            tabu_chk_bnw,
            df_chk_sum,
            df_chk_full_stats,
        )

    return tabu_chk_col, tabu_chk_bnw, df_chk_sum, df_chk_full_stats


# defcheckrnx_analyz
# checkrnx_format
def checkrnx_output(
    output_dir, eporng, tabu_chk_col, tabu_chk_bnw, df_chk_sum, df_chk_full_stats
):

    prefix = "_".join(
        (
            utils.get_timestamp(),
            eporng.epoch_start.strftime("%Y-%j"),
            eporng.epoch_end.strftime("%Y-%j"),
        )
    )

    output_dir_use = utils.create_dir(os.path.join(output_dir, prefix))
    ### csv
    summ_csv = os.path.join(output_dir_use, prefix + "_check_rnx_summ.csv")
    full_csv = os.path.join(output_dir_use, prefix + "_check_rnx_full.csv")
    df_chk_sum.to_csv(summ_csv)
    df_chk_full_stats.to_csv(full_csv)

    ### plot
    df_chk_sum.plot()
    fig = plt.gcf()
    utils.figure_saver(
        fig, output_dir_use, prefix + "_check_rnx_plot", outtype=(".png", ".pdf")
    )
    ### pretty print tabulate
    tabu_col_txt = os.path.join(output_dir_use, prefix + "_check_rnx_tabu_col.txt")
    tabu_bnw_txt = os.path.join(output_dir_use, prefix + "_check_rnx_tabu_bnw.txt")
    utils.write_in_file(tabu_chk_col, tabu_col_txt)
    utils.write_in_file(tabu_chk_bnw, tabu_bnw_txt)
