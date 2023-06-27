#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  2 10:56:52 2023

@author: psakicki
"""

#### Import star style
# geodeZYX modules
from geodezyx import operational as opera
from geodezyx import conv
import pandas as pd
import os 
import rinexmod_api as rma
import datetime  as dt
import numpy as np
import jinja2

import termcolor
import pandas

# # assume `df_out['foo']` is a `pandas.DataFrame` column with
# #     boolean values...
# #
# df = pandas.DataFrame({'foo': [False,True,False,True],
#                        'bar': [False,True,False,True]}) # this is a fake df with
#                                         # no real data.  Ensure 
#                                         # you have a real
#                                         # DataFrame stored in 
#                                         # df...

# # NOTE: there's probably a more idiomatic pandas incantation 
# # for what I'm doing here, but this is intended to 
# # demonstrate the concept of colorizing `colorized_df_out['foo']`
# colorized_df = None
# colored_str_value = ""
# colorized_row = []
# for original_value in df['foo'].values:
#     # casting `original_value` bools as strings to color them red...
#     colored_str_value = termcolor.colored(str(original_value), 'red')
#     colorized_row.append(colored_str_value)
# colorized_df = pandas.DataFrame({'foo': colorized_row})

# print(colorized_df)

def _analyze_rinex(df_in):
    """
    this function do the basic analysis of a DataFrame containing 
    RINEX paths in a "fpath" column

    Parameters
    ----------
    df_in : DataFrame
        DataFrame RINEX paths in a "fpath" column.

    Returns
    -------
    df_out : DataFrame
        Enhanced version of df_in (copied first) with the RINEX infos.
    """
    df_out = df_in.copy()

    ### get RINEX as an rinexMod's Object
    df_out["robj"] = df_out["fpath"].apply(rma.RinexFile)
    ### get RINEX site code
    df_out["site"] = df_out["robj"].apply(lambda r:r.get_site(False,True))
    #sites_all = df_out["site"].unique
    ### get RINEX start/end in the data
    df_out["start"] = df_out["robj"].apply(lambda r:r.start_date)
    df_out["start"] = pd.to_datetime(df_out["start"], format='%H:%M:%S')
    df_out["end"] = df_out["robj"].apply(lambda r:r.end_date)
    df_out["end"] = pd.to_datetime(df_out["end"], format='%H:%M:%S')
    ### get RINEX nominal interval
    df_out["itrvl"] = df_out["robj"].apply(lambda r:r.sample_rate_numeric)
    ### get RINEX number of epochs
    df_out["nepochs"] = df_out["robj"].apply(lambda r:len(r.get_dates_all()))
    ### get completness
    df_out["td_str"] =  df_out["robj"].apply(lambda r:r.get_file_period_from_filename()[0])
    df_out["td_int"] = np.nan
    mask_hour = df_out["td_str"] == "01H"
    df_out.loc[mask_hour,"td_int"] = 3600
    mask_day = df_out["td_str"] == "01D"
    df_out.loc[mask_day,"td_int"] = 86400

    df_out["%"] = (df_out["itrvl"] * df_out["nepochs"] / df_out["td_int"]) * 100
    df_out["%"] = np.round(df_out["%"],0)
    
    ### set flag
    # 0 = OK
    # 1 = missing or critical
    # 2 = incomplete
    df_out["flag"] = np.nan
    df_out.loc[df_out["%"] >= 99., "flag"] = 0
    df_out.loc[df_out["%"] <= 1. , "flag"] = 1
    df_out.loc[(df_out["%"] > 1.) & (df_out["%"] < 99.), "flag"] = 2
    
    return df_out


def _site_missing_in_date(df_dat_in,sites_all):
    """
    Identify the missing RINEX for a date 
    and add they with dummy values in
    a date-grouped DataFrame

    Parameters
    ----------
    df_dat_in : DataFrame
        A date-grouped RINEX DataFrame
        (generated with _analyze_rinex and grouped with .groupby()).
    sites_all : list
        a list of all site possible.

    Returns
    -------
    df_dat_out : DataFrame
        Enhanced version of df_dat_in (copied first) with the missing RINEX

    """
    
    df_dat_out = df_dat_in.copy()
    date = df_dat_out.date.unique()[0]
    
    sites_all = pd.Series(sites_all)
    ### find the site missings ...
    sites_missing = sites_all[np.logical_not(sites_all.isin(df_dat_out.site))]
    
    ### ... add them in thedata frame   
    for sitmis in sites_missing:
        linemis_col = list(df_dat_out.iloc[-1].index)
        
        linemis = pd.Series([None] * len(linemis_col) ,
                            index=linemis_col)
        
        linemis['site'] = sitmis
        linemis['date'] = date
        linemis['start'] = pd.NaT
        linemis['end'] = pd.NaT
        linemis['nepochs'] = 0
        linemis['itrvl'] = np.nan
        linemis['%'] = 0
        linemis["flag"] = 1

        linemis = pd.DataFrame([linemis])
        
        df_dat_out = pd.concat([df_dat_out,
                                linemis],axis=0,
                           ignore_index=True) 
        df_dat_out = df_dat_out.sort_values("site")
        
    return df_dat_out

def _simple_row(df_dat_in):
    """
    Simplfy the date-grouped RINEX DataFrame in a one-line summary with 
    just the completeness ("%")

    Parameters
    ----------
    df_dat_in : DataFrame
        A date-grouped RINEX DataFrame.

    Returns
    -------
    df_simple_out : DataFrame (mono-row)
        One line simplfied version of df_dat_in.

    """
    df_dat_wrk = df_dat_in.copy()
    ser_dat = pd.Series(df_dat_wrk["%"].values,
                        index=df_dat_wrk.site)
    df_simple_out = pd.DataFrame([ser_dat],
                                 index=[df_dat_in.date.unique()[0]])  
    
    
    df_dat_wrk_midx = df_dat_wrk.set_index(["date","site"])
    
    linelissue_stk = []
    
    for date,site_row in df_simple_out.iterrows():
        for site, cplt in site_row.items(): 
            flag = df_dat_wrk_midx.loc[(date,site)].flag
            if flag != 0:
                lineissue = pd.DataFrame([df_dat_wrk_midx.loc[(date,site)]])
                lineissue = lineissue[["start","end","nepochs", "itrvl","%"]]
                linelissue_stk.append(lineissue)
            
    df_issue = pd.concat(linelissue_stk)
    
    return df_simple_out,df_issue


def _row_color_formater(df_simple_in,
                        df_full_in):

        
    color_map = {0:"cyan",
                 1:"red",
                 2:"yellow"}
    
    df_simple_out  = df_simple_in.copy()
    
    df_full_wrk = df_full_in.set_index(["date","site"])
         
    for date,site_row in df_simple_in.iterrows():
        for site, cplt in site_row.items(): 
            flag = df_full_wrk.loc[(date,site)].flag
            color = color_map[flag]
            cplt_color = termcolor.colored(str(cplt),color)
            df_simple_out.loc[date,site] = cplt_color
            
    df_simple_out.columns = [termcolor.colored(x, 'light_grey' , None) for x in df_simple_out.columns]
    
    return df_simple_out
            
####################################'




def check_rinex(rinex_dir,start,end,silent=False,return_concat_df=True):

    list_rnx_all = opera.rinex_finder(p)
    sites_all = pd.Series(list(set([os.path.basename(e)[:4] for e in list_rnx_all])),dtype=str)
    df_all0 = pd.DataFrame(list_rnx_all,columns=["fpath"])
    df_all = df_all0.copy()
    
    df_all["fname"] = df_all["fpath"].apply(os.path.basename)
    df_all["date"] = df_all["fpath"].apply(conv.rinexname2dt)
    
    #### do the date filtering based on start and end
    df_all = df_all[(df_all['date'] >= start) & (df_all['date'] < end)]
    
    
    df_analyze_stk, df_simple_color_stk, df_issue_dat_stk = [],[],[]
    #### Iterate on each date group dataframe
    for date, df_dat0 in df_all.groupby("date"):
        df_dat = df_dat0.copy()
        ### do the analyze of each RINEX content
        df_dat = _analyze_rinex(df_dat)
        ### identify missing sites
        df_dat = _site_missing_in_date(df_dat,sites_all)
        ### create simple one-line version and details of issues 
        df_simple_dat, df_issue_dat = _simple_row(df_dat)
        df_simple_dat_color = _row_color_formater(df_simple_dat,df_dat)

        ### stack everything 
        df_analyze_stk.append(df_dat)        
        df_simple_color_stk.append(df_simple_dat_color)
        df_issue_dat_stk.append(df_issue_dat)

    df_analyze = pd.concat(df_analyze_stk)    
    df_simple_color = pd.concat(df_simple_color_stk)
    df_issue = pd.concat(df_issue_dat_stk)
    
    if return_concat_df:
        df_analyze_out = df_analyze
        df_simple_color_out = df_simple_color
        df_issue_out = df_issue
    else:
        df_analyze_out = df_analyze_stk
        df_simple_color_out = df_simple_color_stk
        df_issue_out = df_issue_dat_stk        
        
    if not silent:
        print(df_simple_color.to_string())
        print(df_issue.to_string())
    
    return df_analyze_out, df_simple_color_out, df_issue_out

    
p="/home/sakic/031_SCRATCH_CONV/052_big_conv_GL_2017/rinexmoded"
start = dt.datetime(2017,3,1)
end = dt.datetime(2017,3,5)

check_rinex(p, start, end)
