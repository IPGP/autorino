#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  8 15:47:58 2024

@author: psakic
"""
import logging
import re

import dateparser
import numpy as np
import pandas as pd
from pandas.tseries.frequencies import to_offset
import datetime as dt

import autorino.common as arocmn
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger("autorino")
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])


def epoch_range_intrpt(epo_inp):
    """
    This function interprets an input to get an output EpochRange object. The input can either be a tuple,
    typically in the form of (epo1, epo2, period), or an instance of the EpochRange class. If the input is
    an EpochRange object, it is returned as is. If the input is a tuple, a new EpochRange object is created
    using the elements of the tuple.

    Parameters
    ----------
    epo_inp : tuple or EpochRange
        The input to be interpreted. If it's a tuple, it should be in the form of (epo1, epo2, period).

    Returns
    -------
    epo_range_out : EpochRange
        The interpreted EpochRange object.
    """
    if type(epo_inp) is arocmn.EpochRange:
        epo_range_out = epo_inp
    elif type(epo_inp) is tuple and len(epo_inp) == 3:
        epo_range_out = arocmn.EpochRange(*epo_inp)
    elif type(epo_inp) is tuple and len(epo_inp) == 2:
        epo_range_out = arocmn.EpochRange(epo_inp[0], epo_inp[1])
    else:
        logger.error("epoch range input not understood")
        raise Exception

    return epo_range_out


def datepars_intrpt(date_inp, tz=None, tz_if_naive="UTC"):
    """
    This function interprets a string or datetime-like object to a Pandas Timestamp.
    It also applies a timezone (UTC by default). Note that rounding does not take place here
    as rounding is not a parsing operation.

    Parameters
    ----------
    date_inp : str or datetime-like
        The input date to be interpreted.
    tz : str, optional
        The timezone to be applied.
        The default is None.
    tz_if_naive : str, optional
        The timezone to be applied if the input date is timezone-naive.
        The default is "UTC".

    Returns
    -------
    date_out : datetime
        The interpreted date as a python native datetime.

    Note
    ----
    If the input date is a string, it is parsed using the dateparser library.
    If the input date is a datetime-like object, it is converted first to a Pandas Timestamp.
    If the resulting date is a NaT (Not a Time) type, it is returned as is.
    If the resulting date does not have a timezone, the specified timezone is applied.
    """
    ### INTERPRET THE INPUT
    if not isinstance(date_inp, str):
        date_out = pd.Timestamp(date_inp)
    ## date_inp is a str
    else:
        ### Must handle the case of day of year separately
        doy_pattern_1 = r"^\d{4}-\d{1,3}$"
        doy_pattern_2 = r"^\d{4}/\d{1.3}$"
        # YYYY-DDD
        if re.match(doy_pattern_1, date_inp):
            date_out = pd.Timestamp(dt.datetime.strptime(date_inp, "%Y-%j"))
        # YYYY/DDD
        elif re.match(doy_pattern_2, date_inp):
            date_out = pd.Timestamp(dt.datetime.strptime(date_inp, "%Y/%j"))
        ### regular case
        else:
            date_out = pd.Timestamp(dateparser.parse(date_inp).isoformat())
            # .isoformat() is to correctly handle the time zone,
            # without weird pytz's objects used by dateparser
            # like <StaticTzInfo 'UTC\+00:00'>

    ### MANAGE THE TIMEZONE
    ### NaT case. can not support tz
    if isinstance(date_out, pd._libs.tslibs.nattype.NaTType):
        return date_out
    ### if the date is timezone-naive, apply the tz_if_naive
    if not date_out.tz:
        logger.warning("date %s is timezone-naive. Applying tz %s", date_out, tz_if_naive)
        date_out = pd.Timestamp(date_out, tz=tz_if_naive)
    ### apply the tz
    if tz:
        date_out = date_out.tz_convert(tz)

    ### OUTPUT A NATIVE DATETIME
    date_out = date_out.to_pydatetime()

    return date_out


def dates_list2epoch_range(dates_list_inp, period=None, round_method="floor"):
    """
    Converts a list of dates to an EpochRange.

    Parameters
    ----------
    dates_list_inp : iterable
        The input list of dates.
    period : str, optional
        The rounding period. If not provided, the period is determined as the unique difference
         between consecutive dates in the input list. The default is None.
    round_method : str, optional
        The method used for rounding the epochs. The default is 'floor'.

    Returns
    -------
    EpochRange
        The converted EpochRange.

    Note
    ----
    The current method for determining the period when not provided is a simple calculation of
    the unique difference between consecutive dates.
    This may not be the most accurate or desired method and should be improved in future iterations of this function.
    """
    epoch1 = np.min(dates_list_inp)
    epoch2 = np.max(dates_list_inp)

    if period:
        period_use = period
    else:
        period_use = np.unique(np.diff(dates_list_inp))[0]  # poor, must be improved

    epo_out = arocmn.EpochRange(
        epoch1, epoch2, period=period_use, round_method=round_method
    )

    return epo_out


def round_date_legacy(date_in, period, round_method="floor"):
    """
    low-level function to round a Pandas Serie or a datetime-like object
    according to the "ceil", "floor", "round", "none" approach

    Parameters
    ----------
    date_in : Pandas Serie or a datetime-like object
        Input date .
    period : str, optional
        the rounding period.
        Use the pandas' frequency aliases convention (see bellow for details).
    round_method : str, optional
        round method: 'ceil', 'floor', 'round', 'none'. The default is "floor".

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

    if pd.isna(date_in):  ### NaT case
        date_out = date_in
    elif isinstance(date_in, pd.Series):
        date_use = date_in

        if round_method == "ceil":
            date_out = date_use.dt.ceil(period)
        elif round_method == "floor":
            date_out = date_use.dt.floor(period)
        elif round_method == "round":
            date_out = date_use.dt.round(period)
        elif round_method == "none":
            date_out = date_use
        else:
            logger.critical("round_method not understood")
            raise Exception
    else:
        date_typ = type(date_in)
        if date_typ in (pd.Timedelta,):
            date_use = pd.Timedelta(date_in)
        else:
            date_use = pd.Timestamp(date_in)

        if round_method == "ceil":
            date_out = date_use.ceil(period)
        elif round_method == "floor":
            date_out = date_use.floor(period)
        elif round_method == "round":
            date_out = date_use.round(period)
        elif round_method == "none":
            date_out = date_use
        else:
            logger.critical("round_method not understood")
            raise Exception

        #++++ back to the original type
        if date_typ in (dt.datetime,):
            date_out = date_out.to_pydatetime()
        else:
            date_out = date_typ(date_out)

    return date_out


def round_date(date_in, period, round_method="floor"):
    """
    low-level function to round a Pandas Serie or a datetime-like object
    according to the "ceil", "floor", "round", "none" approach

    Parameters
    ----------
    date_in : Pandas Serie or a datetime-like object
        Input date .
    period : str, optional
        the rounding period.
        Use the pandas' frequency aliases convention (see bellow for details).
    round_method : str, optional
        round method: 'ceil', 'floor', 'round', 'none'. The default is "floor".

    Returns
    -------
    date_out : Pandas Serie or datetime-like object (same as input)
        rounded date.

    Note
    ----
    Pandas' frequency aliases memo
    https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases

    """

    # ++++ NaT case
    if pd.isna(date_in):
        return date_in

    # ++++ Series case
    if isinstance(date_in, pd.Series):
        return getattr(date_in.dt, round_method)(period)

    # ++++ Singleton case
    date_use = pd.Timedelta(date_in) if isinstance(date_in, pd.Timedelta) else pd.Timestamp(date_in)
    date_out = getattr(date_use, round_method)(period) if round_method != "none" else date_use

    # ++++ back to the original type
    date_out = date_out.to_pydatetime() if isinstance(date_in, dt.datetime) else type(date_in)(date_out)

    return date_out


def round_epochs(
    epochs_inp, period="1d", rolling_period=False, rolling_ref=-1, round_method="floor"
):
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
        Whether to use a rolling period for splicing the RINEX files.
        If False, the spliced files will be based only on the "full" period provided,
        i.e. Day1 00h-24h, Day2 00h-24h, etc.
        If True, the spliced files will be based on the rolling period.
        i.e. Day1 00h-Day2 00h, Day1 01h-Day2 01h, Day1 02h-Day2 02h etc.
        Defaults to False.
    rolling_ref :  datetime-like or int, optional
        The reference for the rolling period.
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
        epochs_rnd = arocmn.round_date(epochs_use, period, round_method)
    else:
        if type(rolling_ref) is int:
            rolling_ref_use = epochs_use.iloc[rolling_ref]
        else:
            rolling_ref_use = rolling_ref

        ### add one second to be sure that the rolling_ref is included in a group
        rolling_ref_use = rolling_ref_use + np.timedelta64(1, "s")

        roll_diff = epochs_use - rolling_ref_use

        epochs_rnd = (
            arocmn.round_date(roll_diff, period, round_method) + rolling_ref_use
        )

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

    epo = arocmn.EpochRange(epoch1=pd.NaT, epoch2=pd.NaT, period="15min")
    return epo


def iso_zulu_epoch(epo_in):
    """
    Convert an input epoch to ISO 8601 format with Zulu time (UTC).

    Parameters
    ----------
    epo_in : datetime-like
        The input epoch to be converted.

    Returns
    -------
    str
        The epoch in ISO 8601 format with Zulu time (UTC).
    """
    return pd.Timestamp(epo_in).isoformat().replace("+00:00", "Z")
