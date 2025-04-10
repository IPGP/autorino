#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  8 15:47:58 2024

@author: psakic

This module, eporng_cls.py, provides a class for handling ranges of epochs.
"""

import re

import numpy as np
import pandas as pd
from geodezyx import utils

import autorino.common as arocmn

#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger("autorino")
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])


class EpochRange:
    """
    A class used to represent a range of epochs.

    ...

    Attributes
    ----------
    period : str
        the rounding period. Use the pandas' frequency aliases convention.
    round_method : str
        the method used for rounding the epochs.
    tz : str
        the timezone used for the epochs.
    _epoch1_raw : datetime
        the raw start of the epoch range.
    _epoch2_raw : datetime
        the raw end of the epoch range.

    Methods
    -------
    eporng_list(end_bound=False):
        Computes the list of epochs corresponding to the EpochRange.
    is_valid():
        Checks if the epoch range is valid.
    """

    def __init__(
        self, epoch1, epoch2=None, period="1d", round_method="floor", tz="UTC"
    ):
        """
        Constructs all the necessary attributes for the epoch range object.

        Parameters
        ----------
            epoch1 : str, datetime, pd.Timestamp, pd.NaT, list
                the start of the epoch range.
            epoch2 : str, datetime, pd.Timestamp, pd.NaT
                the end of the epoch range.
            period : str, optional
                the rounding period. Use the pandas' frequency aliases convention.
            round_method : str, optional
                the method used for rounding the epochs.
            tz : str, optional
                the timezone used for the epochs.
        """

        self._epoch1_raw = epoch1
        self._epoch2_raw = epoch2

        self.period = period
        self.round_method = round_method
        self.tz = tz

        if (
            self._epoch1_raw and self._epoch2_raw
        ):  # 1) regular case: a start and an end are given
            _epoch1tmp = arocmn.datepars_intrpt(self._epoch1_raw)
            _epoch2tmp = arocmn.datepars_intrpt(self._epoch2_raw)
            _epoch_min_tmp = np.min((_epoch1tmp, _epoch2tmp))
            _epoch_max_tmp = np.max((_epoch1tmp, _epoch2tmp))

            self.epoch_start = _epoch_min_tmp  ### setter bellow
            self.epoch_end = _epoch_max_tmp  ### setter bellow

            self.manual_range = False
            self._manu_range_list = []

        elif (
            utils.is_iterable(self._epoch1_raw) and not self._epoch2_raw
        ):  # 2) case a start is given as a list, but no end
            _epoch1tmp = [arocmn.datepars_intrpt(e) for e in self._epoch1_raw]
            _epoch_min_tmp = np.min(_epoch1tmp)
            _epoch_max_tmp = np.max(_epoch1tmp)

            self.epoch_start = _epoch_min_tmp
            self.epoch_end = _epoch_max_tmp

            self.manual_range = True
            self._manu_range_list = _epoch1tmp

    ## NB: I think it is a bad idea to have an attribute (property) to get the list of epochs

    def __repr__(self):
        return "from {} to {}, period {}".format(
            arocmn.iso_zulu_epoch(self.epoch_start),
            arocmn.iso_zulu_epoch(self.epoch_end),
            self.period,
        )

    ############ getters and setters
    @property
    def epoch_start(self):
        """Gets the start of the epoch range."""
        return self._epoch_start

    @epoch_start.setter
    def epoch_start(self, value):
        """Sets the start of the epoch range."""
        self._epoch_start = arocmn.datepars_intrpt(value, tz=self.tz)
        self._epoch_start = arocmn.round_date(
            self._epoch_start, self.period, self.round_method
        )

    @property
    def epoch_end(self):
        """Gets the end of the epoch range."""
        return self._epoch_end

    @epoch_end.setter
    def epoch_end(self, value):
        """Sets the end of the epoch range."""
        self._epoch_end = arocmn.datepars_intrpt(value, tz=self.tz)
        self._epoch_end = arocmn.round_date(
            self._epoch_end, self.period, self.round_method
        )

    @property
    def period_values(self):
        """
        For a period, e.g. 15min, 1H...
        Returns the value (e.g. 15, 1) and the unit (e.g. min, H)
        """
        numbers = re.findall(r"[0-9]+", self.period)
        alphabets = re.findall(r"[a-zA-Z]+", self.period)
        val = int("".join(*numbers))
        unit = str("".join(*alphabets))
        return val, unit

    @property
    def period_as_timedelta(self):
        """
        For a period, e.g. 15min, 1H...
        return in as a pandas Timedelta
        """
        return pd.Timedelta(self.period)

    ########### methods
    def eporng_list(self, end_bound=False):
        """
        Compute the list of epochs corresponding to the EpochRange.

        Parameters
        ----------
        end_bound : bool, optional
            If True, gives the end bound of the range. Default is False.

        Returns
        -------
        list
            List of epochs.
        """
        if self.manual_range:
            return self.eporng_list_manual(end_bound=end_bound)
        else:
            return self.eporng_list_regular(end_bound=end_bound)

    def eporng_list_manual(self, end_bound=False):
        """
        Compute the list of epochs for a forced range.

        Parameters
        ----------
        end_bound : bool, optional
            If True, gives the end bound of the range. Default is False.

        Returns
        -------
        list
            List of epochs.
        """
        if not self.eporng_list_manual:
            logger.error("No forced range list available")
            return []

        if not end_bound:
            return self._manu_range_list
        else:
            # subtract also one second for security reason
            plus_one = pd.Timedelta(self.period)
            return list(np.array(self._manu_range_list) + plus_one - pd.Timedelta("1s"))

    def eporng_list_regular(self, end_bound=False):
        """
        Compute the list of epochs corresponding to the EpochRange
        if end_bound = True, give the end bound of the range
        (start bound is generated per default)

        Parameters
        ----------
        end_bound : bool, optional
            If True, gives the end bound of the range.

        Returns
        -------
        list
            List of epochs.
        """
        if not self.is_valid():  ### NaT case
            eporng = [pd.NaT]
        elif not end_bound:  ### start bound
            eprrng_srt = pd.date_range(
                self.epoch_start, self.epoch_end, freq=self.period
            )
            eporng = eprrng_srt
        else:  ### end bound
            plus_one = self.period_as_timedelta
            eprrng_end = pd.date_range(
                self.epoch_start, self.epoch_end + plus_one, freq=self.period
            )
            # subtract also one second for security reason
            # first element is the epoch start, thus we remove it
            eporng = eprrng_end[1:] - np.timedelta64(1, "s")

        return list(eporng)

    def is_valid(self):
        """
        Checks if the epoch range is valid.

        Returns
        -------
        bool
            True if the epoch range is valid, False otherwise.
        """
        if pd.isna(self.epoch_start) or pd.isna(self.epoch_end):
            return False
        else:
            return True


    def extra_margin_splice(self):
        """
        Returns the extra margin for splicing operations.

        Leica raw files  can be a bit over their nominal end,
        so we need to add a margin to the splicing operation.

        Returns
        -------

        """
        if self.period_as_timedelta >= pd.Timedelta("1 day"):
            return pd.Timedelta("1 hour")
        else:
            return pd.Timedelta("1 minute")
