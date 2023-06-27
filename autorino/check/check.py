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
import numpy as np

import termcolor
import pandas

# Create a logger object.
import logging
logger = logging.getLogger(__name__)


def check_rinex(rinex_dir,start,end,silent=False,return_concat_df=False):
    """
    Frontend to check the validity of RINEXs (downloaded/converted)
    
    DataFrame tables are returned to gives an overview of the RINEXs

    Parameters
    ----------
    rinex_dir : str
        parent directory of a RINEX archive.
        the complete directory and sub-dirs. will be crawled
    start : datetime
        start date of the wished period.
    end : datetime
        end date of the wished period.
    silent : bool, optional
        do not print the tables in the console
        The default is False (tables will be printed).
    return_concat_df : bool, optional
        Instead of a daily print of the tables,
        all the analyzed days are stacked in single tables.
        Result is slower but more pretty.
        The default is False.
        
    Returns
    -------
    df_analyze_out : DataFrame
        A Table with all the details of the analyzed RINEXs.
    df_simple_color_out : DataFrame
        A synoptic Table with simply the completeness of analyzed RINEXs.
    df_issue_out : DataFrame
        A detailed Table for the problematic analyzed RINEXs.

    """
        
    list_rnx_all = opera.rinex_finder(rinex_dir)
    
    char4_all_list = list(set([os.path.basename(e)[:4] for e in list_rnx_all]))
    sites_all = pd.Series(char4_all_list,dtype=str)
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
        
        if not silent and not return_concat_df:
            prefix = " for {} \n".format(date)
            logger.info("RINEXs summary" + prefix + df_simple_dat_color.to_string())
            logger.info("RINEXs issues" + prefix + df_issue_dat.to_string())

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
        
    if not silent and return_concat_df:
        prefix = " for period {} - {} \n".format(start,end)
        logger.info("RINEXs summary" + prefix + df_simple_color.to_string())
        logger.info("RINEXs issues" + prefix + df_issue.to_string())
    
    
    return df_analyze_out, df_simple_color_out, df_issue_out


##############################################################################
#### Inner functions


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
        
    Note
    ----
    Flags meaning
    
    * 0 = OK
    * 1 = missing RINEX or critical content
    * 2 = incomplete RINEX
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
    
    cols_lineissue = ["start","end","nepochs", "itrvl","%"]
    
    for date,site_row in df_simple_out.iterrows():
        for site, cplt in site_row.items(): 
            flag = df_dat_wrk_midx.loc[(date,site)].flag
            if flag != 0:
                lineissue = pd.DataFrame([df_dat_wrk_midx.loc[(date,site)]])
                lineissue = lineissue[cols_lineissue]
                linelissue_stk.append(lineissue)
    
    if linelissue_stk:
        df_issue = pd.concat(linelissue_stk)
    else:
        df_issue = pd.DataFrame(columns=cols_lineissue) # no issue :)
    
    return df_simple_out,df_issue


def _row_color_formater(df_simple_in,
                        df_full_in):
    """
    Format a df_simple DataFrame with colors
    Need df_full_ in to gat the flags values
    """
        
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
            
####################################
