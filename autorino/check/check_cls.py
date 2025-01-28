#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 27/01/2025 09:35:53

@author: psakic
"""
import pandas as pd
import numpy as np

import autorino.handle as arohdl
import autorino.check as arochk
import rinexmod
import tqdm


class CheckGnss(arohdl.HandleGnss):
    def __init__(
        self,
        out_dir=None,
        tmp_dir=None,
        log_dir=None,
        inp_dir=None,
        inp_file_regex=None,
        epoch_range=None,
        site=None,
        session=None,
        options=None,
        metadata=None,
    ):

        super().__init__(
            out_dir=out_dir,
            tmp_dir=tmp_dir,
            log_dir=log_dir,
            inp_dir=inp_dir,
            inp_file_regex=inp_file_regex,
            epoch_range=epoch_range,
            site=site,
            session=session,
            options=options,
            metadata=metadata,
        )

        self.table_stats = pd.DataFrame()

    def analyze_rnxs2(self):
        """
        this function do the basic analysis of the table of RINEXs

        Note
        ----
        Flags meaning

        * 0 = OK
        * 1 = missing RINEX or critical content
        * 2 = incomplete RINEX
        """


        self.table_stats = pd.DataFrame()

        dfts = self.table_stats
        dfts["fpath"] = self.table["fpath_inp"]

        ### get RINEX as an rinexMod's Object
        dfts["robj"] = dfts["fpath"].apply(rinexmod.rinexfile.RinexFile)
        ### get RINEX site code
        dfts["site"] = dfts["robj"].apply(lambda r: r.get_site(False, True))
        # sites_all = dfts["site"].unique
        ### get RINEX start/end in the data
        dfts["start"] = dfts["robj"].apply(lambda r: r.start_date)
        dfts["start"] = pd.to_datetime(dfts["start"], format='%H:%M:%S')
        dfts["end"] = dfts["robj"].apply(lambda r: r.end_date)
        dfts["end"] = pd.to_datetime(dfts["end"], format='%H:%M:%S')
        ### get RINEX nominal interval
        dfts["itrvl"] = dfts["robj"].apply(lambda r: r.sample_rate_numeric)
        ### get RINEX number of epochs
        dfts["nepochs"] = dfts["robj"].apply(lambda r: len(r.get_dates_all()))
        ### get completness
        dfts["td_str"] = dfts["robj"].apply(lambda r: r.get_file_period_from_filename()[0])


        dfts["td_int"] = np.nan
        mask_hour = dfts["td_str"] == "01H"
        dfts.loc[mask_hour, "td_int"] = 3600
        mask_day = dfts["td_str"] == "01D"
        dfts.loc[mask_day, "td_int"] = 86400

        dfts["%"] = (dfts["itrvl"] * dfts["nepochs"] / dfts["td_int"]) * 100
        dfts["%"] = np.round(dfts["%"], 0)

        ### set flag
        # 0 = OK
        # 1 = missing or critical
        # 2 = incomplete
        dfts["flag"] = np.nan
        dfts.loc[dfts["%"] >= 99., "flag"] = 0
        dfts.loc[dfts["%"] <= 1., "flag"] = 1
        dfts.loc[(dfts["%"] > 1.) & (dfts["%"] < 99.), "flag"] = 2

        return dfts

    def analyze_rnxs(self):
        """
        this function do the basic analysis of the table of RINEXs

        Note
        ----
        Flags meaning

        * 0 = OK
        * 1 = missing RINEX or critical content
        * 2 = incomplete RINEX
        """

        self.table_stats = pd.DataFrame()

        ds_stk = []

        for irow, row in tqdm.tqdm(self.table.iterrows(), total=len(self.table),
                                   desc="Analyzing RINEX files for " + self.site_id):

            ds = dict()
            ds["fpath"] = self.table.loc[irow, "fpath_inp"]
            ds["site"] = self.table.loc[irow, "site"]

            if not self.mono_ok_check(int(irow), 'check'):
                ds["%"] = 0
            else:
                ### get RINEX as an rinexMod's Object
                rnxobj = rinexmod.rinexfile.RinexFile(ds["fpath"])
                ### get RINEX site code
                ds["site"] = rnxobj.get_site(lower_case=False, only_4char=False)

                ### theoretical epochs
                ds["epoch_srt"] = self.table.loc[irow, "epoch_srt"]
                ds["epoch_end"] = self.table.loc[irow, "epoch_end"]

                ### get RINEX start/end in the data
                ds["epoch_srt_data"] = pd.to_datetime(rnxobj.start_date, format='%H:%M:%S')
                ds["epoch_end_data"] = pd.to_datetime(rnxobj.end_date, format='%H:%M:%S')
                ### get RINEX nominal interval
                ds["itrvl"] = rnxobj.sample_rate_numeric
                ### get RINEX number of epochs
                ds["nepochs"] = len(rnxobj.get_dates_all())
                ### get completness
                ds["td_str"] = rnxobj.get_file_period_from_filename()[0]

                # improve with right fct !!!!
                if ds["td_str"] == "01H":
                    ds["td_int"] = 3600
                elif ds["td_str"] == "01D":
                    ds["td_int"] = 86400
                else:
                    ds["td_int"] = np.nan

                ds["%"] = (ds["itrvl"] * ds["nepochs"] / ds["td_int"]) * 100
                ds["%"] = np.round(ds["%"], 0)

            ds_stk.append(ds)

        dfts = pd.DataFrame(ds_stk)
        self.table_stats = dfts

        return dfts


    def check(self):
        self.guess_local_rnx(io="inp")
        self.check_local_files(io="inp")
        self.print_table()
        self.analyze_rnxs()
        self.table["%"] = self.table_stats["%"]


