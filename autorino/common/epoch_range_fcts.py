#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  8 15:47:58 2024

@author: psakicki
"""

#### Import star style
import dateparser
import datetime as dt
import pandas as pd
import numpy as np
import re
from pandas.tseries.frequencies import to_offset

def dateparser_frontend(date_inp, tz="UTC"):
    """
    Frontend function to parse a string/datetime
    to a Pandas Timestamp
    (standard used for the DownloadGnss object)
    Also apply a timezone (UTC per default)

    NB: the rounding will not take place here
    rounding is not a parsing operation
    """

    if type(date_inp) is str:
        date_out = pd.Timestamp(dateparser.parse(date_inp))
    else:
        date_out = pd.Timestamp(date_inp)

    if type(date_out) is pd._libs.tslibs.nattype.NaTType:
        ### NaT case. can not support tz
        pass
    elif not date_out.tz:
        date_out = pd.Timestamp(date_out, tz=tz)

    return date_out

def dates_list2epoch_range(dates_list_inp,
                           period=None,
                           round_method='floor'):
    epoch1 = np.min(dates_list_inp)
    epoch2 = np.max(dates_list_inp)

    if period:
        period_use = period
    else:
        period_use = np.unique(np.diff(dates_list_inp))[0]  ### poor, must be improved

    epo_out = EpochRange(epoch1, epoch2, period=period_use, round_method=round_method)

    return epo_out


def _round_date(date_in, period, round_method="round"):
    """
    low-level function to round a Pandas Serie or a datetime-like object
    according to the "ceil", "floor" or "round" approach

    Parameters
    ----------
    date_inp : Pandas Serie or a datetime-like object
        Input date .
    period : str, optional
        the rounding period.
        Use the pandas' frequency aliases convention (see bellow for details).
    round_method : str, optional
        round method: 'ceil', 'floor', 'round'. The default is "floor".

    Returns
    -------
    date_out : Pandas Serie or datetime-like object (same as input)
        rounded date.

    Note
    ----
    Pandas' frequency aliases memo
    https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases

    """

    # we separate the Series case of the simple datetime-like
    # both for ease and performance reason

    if type(date_in) is pd._libs.tslibs.nattype.NaTType:  ### NaT case
        date_out = date_in

    elif type(date_in) is pd.Series:

        date_use = date_in

        if round_method == "ceil":
            date_out = date_use.dt.ceil(period)
        elif round_method == "floor":
            date_out = date_use.dt.floor(period)
        elif round_method == "round":
            date_out = date_use.dt.round(period)
        else:
            raise Exception

    else:
        date_typ = type(date_in)
        date_use = pd.Timestamp(date_in)

        if round_method == "ceil":
            date_out = date_use.ceil(period)
        elif round_method == "floor":
            date_out = date_use.floor(period)
        elif round_method == "round":
            date_out = date_use.round(period)
        else:
            raise Exception

        date_out = date_typ(date_out)

    return date_out


def round_epochs(epochs_inp,
                 period='1d',
                 rolling_period=False,
                 rolling_ref=-1,
                 round_method='floor'):
    """
    High-level function to round several epochs to a common one.
    Useful to group and then splice RINEX

    Use it with pandas .groupby in a further step

    Parameters
    ----------
    epochs_inp : iterable
        The input epochs expected to be rounded.
    period : str, optional
        the rounding period.
        Use the pandas' frequency aliases convention (see bellow for details).
        The default is '1d'.
    rolling_period : bool, optional
        The rounding depends on a reference epoch defined with rolling_ref.
        The default is False.
    rolling_ref : datetime-like or int, optional
        If datetime-like object, use this epoch as reference.
        If integer, use the epoch of the corresponding index
        Use -1 for the last epoch for instance.
        The default is -1.
    round_method : str, optional
        round method: 'ceil', 'floor', 'round'. The default is "floor".

    Returns
    -------
    epochs_rnd :
        Pandas Series of Timestamp or Timedelta

    Note
    ----
    Pandas' frequency aliases memo
    https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases

    """

    epochs_use = pd.Series(epochs_inp)

    if not rolling_period:
        epochs_rnd = _round_date(epochs_use, period, round_method)
    else:
        if type(rolling_ref) is int:
            rolling_ref_use = epochs_use.iloc[rolling_ref]
        else:
            rolling_ref_use = rolling_ref

        ### add one second to be sure that the rolling_ref is included in a group
        rolling_ref_use = rolling_ref_use + np.timedelta64(1, 's')

        roll_diff = epochs_use - rolling_ref_use
        epochs_rnd = _round_date(roll_diff, period, round_method)

    return epochs_rnd


def timedelta2freq_alias(timedelta_in):
    """
    Time representation conversion

    Timedelta (from datetime, numpy or pandas) => Pandas' Frequency alias

    Parameters
    ----------
    timedelta_in : timedelta-like
        POSIX Time.  Can *NOT YET* handle several timedelta in a list.

    Returns
    -------
    offset : string
        Converted pandas' frequency alias

    Note
    ----
    Pandas' frequency aliases memo
    https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases
    """

    offset = to_offset(pd.Timedelta(timedelta_in))
    return offset.freqstr


def create_dummy_epochrange():
    """
    Create a fake/dummy EpochRange object
    for test/development purpose

    Returns
    -------
    ses : EpochRange object
        dummy EpochRange object.

    """

    epo = EpochRange(epoch1="24 hours and 30min ago",
                     epoch2="30 min ago",
                     period='15min')
    return epo