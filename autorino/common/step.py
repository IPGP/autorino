#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  8 16:53:51 2024

@author: psakic
"""

# Import the logger
import logging
import shutil

import pandas as pd
import numpy as np
import os
import re
import copy

import rinexmod
from geodezyx import utils, conv, operational

import autorino.common as arocmn
import autorino.config as arocfg

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")


class StepGnss():
    def __init__(self,
                 out_dir, tmp_dir, log_dir,
                 epoch_range=None,
                 site=None,
                 session=None,
                 options=None):

        self._init_epoch_range(epoch_range)
        self._init_site(site)
        self._init_session(session)
        self._init_options(options)
        self._init_site_id()
        self._init_table()

        self.translate_dict = self._set_translate_dict()
        self.out_dir = out_dir
        self.tmp_dir = tmp_dir
        self.log_dir = log_dir

        # generic log
        self.set_logfile()
        # table log is on request only (for the moment9)
        # thus this table_log_path attribute must be initialized as none
        self.table_log_path = None

    def __repr__(self):
        name = type(self).__name__
        out = "{} {}/{}".format(name,
                                self.site_id,
                                self.epoch_range)
        return out

    # getter and setter
    # site_id

    @property
    def out_dir(self):
        return self.translate_path(self._out_dir)

    @out_dir.setter
    def out_dir(self, value):
        self._out_dir = value

    @property
    def tmp_dir(self):
        return self.translate_path(self._tmp_dir)

    @tmp_dir.setter
    def tmp_dir(self, value):
        self._tmp_dir = value

    @property
    def log_dir(self):
        return self.translate_path(self._log_dir)

    @log_dir.setter
    def log_dir(self, value):
        self._log_dir = value

    @property
    def site_id(self):
        return self._site_id

    @site_id.setter
    def site_id(self, value):
        self._site_id = value

    @property
    def site_id4(self):
        return self._site_id[:4]

    @property
    def site_id9(self):
        if len(self._site_id) == 9:
            return self._site_id
        elif len(self._site_id) == 4:
            return self._site_id + "00XXX"
        else:
            return self._site_id[:4] + "00XXX"

    #     return self._site_id9
    # @site_id9.setter
    # def site_id9(self,value):
    #     if len(value) == 9:
    #         self._site_id9 = value
    #     elif len(value) == 4:
    #         self._site_id9 = value + "00XXX"
    #     else:
    #         raise Exception("given site code != 9 or 4 chars.: " + value)

    # epoch_range

    @property
    def epoch_range(self):
        return self._epoch_range

    @epoch_range.setter
    def epoch_range(self, value):
        self._epoch_range = value
        # this test becomes useless after session class suppression (240126)
        # if self._epoch_range.period != self.session.session_period:
        #     logger.warning("Session period (%s) ≠ Epoch Range period (%s)",
        #     self.session.session_period,self._epoch_range.period)

    # table
    @property
    def table(self):
        return self._table

    @table.setter
    def table(self, value):
        self._table = value
        # designed for future safety tests

    def _init_table(self,
                    table_cols: list = None,
                    init_epoch: bool = True):
        """
        initialize the table of a Step object

        Parameters
        ----------
        table_cols
        init_epoch: bool

        """

        if table_cols is None:
            table_cols = ['fname',
                          'site',
                          'epoch_srt',
                          'epoch_end',
                          'ok_inp',
                          'ok_out',
                          'fpath_inp',
                          'fpath_out',
                          'size_inp',
                          'size_out',
                          'note']

        df = pd.DataFrame([], columns=table_cols)

        if init_epoch:
            df['epoch_srt'] = self.epoch_range.epoch_range_list()
            df['epoch_end'] = self.epoch_range.epoch_range_list(end_bound=True)

            df['site'] = self.site_id

        self.table = df
        return None

    def _init_site(self, site):
        """
        if a site dict is not given, create a dummy one
        """

        if not site:
            logger.warning('no site dict given, a dummy one will be created')
            self.site = create_dummy_site_dic()
        else:
            self.site = site

        return None

    def _init_session(self, session):
        """
        if a session dict is not given, create a dummy one
        """

        if not session:
            logger.warning(
                'no session dict given, a dummy one will be created')
            self.session = create_dummy_session_dic()
        else:
            self.session = session

        return None


    def _init_options(self, options):
        """
        if a options dict is not given, create an empty one
        """

        if not options:
            self.options = {}
        else:
            self.options = options

        return None

    def _init_site_id(self):
        """
        if a site id is not explicitly given, take the one from the site dict
        A dummy site dict will be created in the worst case, ensuring that
        site_id will be always initialized
        """
        if 'site_id' in self.site.keys():
            self.site_id = self.site['site_id']
        else:
            self.site_id = 'XXXX'

        return None

    def _init_epoch_range(self, epoch_range):
        """
        initialize the epoch range if given, and create a dummy one between 
        NaT (not a time) if nothing is given
        """
        if epoch_range:
            self.epoch_range = epoch_range
        else:
            self.epoch_range = arocmn.EpochRange(pd.NaT,pd.NaT)

        return None

    def _set_translate_dict(self):
        """
        generate the translation dict based on the access and session dicts
        object attributes + site id

        site code have 2x3 declinations:
        <site_id(4|9|)> (lowercase) and <SITE_ID(4|9|)> (uppercase)
        """
        trsltdict = dict()

        for dic in (self.site,
                    self.session):
            for k, v in dic.items():
                trsltdict[k] = v

        # site have a specific loop
        for s in ('site_id', 'site_id4', 'site_id9'):
            trsltdict[s.upper()] = str(getattr(self, s)).upper()
            trsltdict[s.lower()] = str(getattr(self, s)).lower()

        return trsltdict

    def _init_tmp_dirs_paths(self,
                             tmp_subdir_logs='logs',
                             tmp_subdir_unzip='unzipped',
                             tmp_subdir_conv='converted',
                             tmp_subdir_rnxmod='rinexmoded'):
        """
        initialize temp dirs, but keeps their generic form, with <...> and %X,
        and without creating them

        see set_tmp_dirs_paths() for the effective translation and
        creation of these temp dirs
        """

        ### internal (_) versions have not been translated
        self._tmp_dir_logs = os.path.join(self.tmp_dir,
                                          tmp_subdir_logs)
        self._tmp_dir_unzipped = os.path.join(self.tmp_dir,
                                              tmp_subdir_unzip)
        self._tmp_dir_converted = os.path.join(self.tmp_dir,
                                               tmp_subdir_conv)
        self._tmp_dir_rinexmoded = os.path.join(self.tmp_dir,
                                                tmp_subdir_rnxmod)

        ### translation
        self.tmp_dir_logs = self.translate_path(self._tmp_dir_logs)
        self.tmp_dir_unzipped = self.translate_path(self._tmp_dir_unzipped)
        self.tmp_dir_converted = self.translate_path(self._tmp_dir_converted)
        self.tmp_dir_rinexmoded = self.translate_path(self._tmp_dir_rinexmoded)

        return None

    def set_tmp_dirs_paths(self):
        """
        effective translation and creation of temp dirs
        """
        #### this translation is also done in _init_tmp_dirs_paths
        tmp_dir_logs_set = self.translate_path(self._tmp_dir_logs)
        tmp_dir_unzipped_set = self.translate_path(self._tmp_dir_unzipped)
        tmp_dir_converted_set = self.translate_path(self._tmp_dir_converted)
        tmp_dir_rinexmoded_set = self.translate_path(self._tmp_dir_rinexmoded)

        utils.create_dir(tmp_dir_logs_set)
        utils.create_dir(tmp_dir_unzipped_set)
        utils.create_dir(tmp_dir_converted_set)
        utils.create_dir(tmp_dir_rinexmoded_set)

        return tmp_dir_logs_set, tmp_dir_unzipped_set, \
            tmp_dir_converted_set, tmp_dir_rinexmoded_set

    #   _____                           _                  _   _               _
    #  / ____|                         | |                | | | |             | |
    # | |  __  ___ _ __   ___ _ __ __ _| |  _ __ ___   ___| |_| |__   ___   __| |___
    # | | |_ |/ _ \ '_ \ / _ \ '__/ _` | | | '_ ` _ \ / _ \ __| '_ \ / _ \ / _` / __|
    # | |__| |  __/ | | |  __/ | | (_| | | | | | | | |  __/ |_| | | | (_) | (_| \__ \
    #  \_____|\___|_| |_|\___|_|  \__,_|_| |_| |_| |_|\___|\__|_| |_|\___/ \__,_|___/

    def copy(self):
        """
        return a duplicate (deep copy) of the current StepGnss object
        """
        return copy.deepcopy(self)

    def get_step_type(self):
        return type(wkf).__name__

    def update_epoch_table_from_rnx_fname(self,
                                          use_rnx_filename_only=False,
                                          update_epoch_range=True):
        """
        If the StepGnss object **contains RINEX files**,
        Update the StepGnss table's columns ``epoch_srt`` and ``epoch_end``
        based on the RINEX files.

        Parameters
        ----------
        use_rnx_filename_only : bool, optional
            determine the start epochm the end epoch and the period of the
            RINEX file based on its name only. (The RINEX is not readed).
            This function is much faster but less reliable.
            The default is False.
        update_epoch_range : bool, optional
            at the end of the table update, update also
            the EpochRange object associated to the StepGnss object
            (recommended).
            The default is True.

        Returns
        -------
        None.

        """

        is_rnx = \
            self.table['fname'].apply(
                conv.rinex_regex_search_tester).apply(bool)

        if is_rnx.sum() == 0:
            logger.warning("epoch update impossible, \
                        no file matches a RINEX pattern in %s", self)
            return

        for irow, row in self.table.iterrows():

            if not use_rnx_filename_only:
                rnx = rinexmod.rinexfile.RinexFile(row['fpath_inp'])
                epo_srt = rnx.start_date
                epo_end = rnx.end_date
            else:
                epo_srt, epo_end, _ = \
                    rinexmod.rinexfile.dates_from_rinex_filename(
                        row['fpath_inp'])

            self.table.loc[irow, 'epoch_srt'] = epo_srt
            self.table.loc[irow, 'epoch_end'] = epo_end

        self.table['epoch_srt'] = pd.to_datetime(self.table['epoch_srt'])
        self.table['epoch_end'] = pd.to_datetime(self.table['epoch_end'])

        if update_epoch_range:
            self.update_epoch_range_from_table()

        return

    def update_epoch_range_from_table(self,
                                      column_srt='epoch_srt',
                                      column_end = 'epoch_end'):
        """
        update the EpochRange of the StepGnss object with
        the min/max of the epochs in the object's table
        """
        epomin = self.table[column_srt].min()
        epomax = self.table[column_srt].max()

        epoch1 = epomin
        epoch2 = epomax

        tdelta = self.table[column_end] - self.table[column_srt]

        n_tdelta = tdelta.value_counts().to_frame()
        v_tdelta = tdelta.mode()[0]

        if len(n_tdelta) > 1:
            logger.warning("the period spacing of %s is not uniform, keep the most common", self)
            logger.warning("%s", n_tdelta)
            # be sure to keep the 1st one!!!

        period_new = arocmn.timedelta2freq_alias(v_tdelta)
        logger.debug("new period, %s, %s",v_tdelta, period_new)

        self.epoch_range = arocmn.EpochRange(epoch1,epoch2,period_new,
                                             round_method=self.epoch_range.round_method,
                                             tz=self.epoch_range.tz)

        logger.info("new %s", self.epoch_range)

    def translate_path(self, path_inp, epoch_inp=None):
        return arocmn.translator(path_inp, self.translate_dict, epoch_inp)

    #  _                       _
    # | |                     (_)
    # | |     ___   __ _  __ _ _ _ __   __ _
    # | |    / _ \ / _` |/ _` | | '_ \ / _` |
    # | |___| (_) | (_| | (_| | | | | | (_| |
    # |______\___/ \__, |\__, |_|_| |_|\__, |
    #               __/ | __/ |         __/ |
    #              |___/ |___/         |___/

    def set_logfile(self,
                    log_dir_inp=None,
                    step_suffix=''):
        """
        set logging in a file
        """

        if not log_dir_inp:
            log_dir = self.log_dir
        else:
            log_dir = log_dir_inp

        log_dir_use = self.translate_path(log_dir)

        _logger = logging.getLogger('autorino')

        ts = utils.get_timestamp()
        log_name = "_".join((ts, step_suffix, ".log"))
        log_path = os.path.join(log_dir_use, log_name)

        log_cfg_dic = arocfg.logcfg.log_config_dict
        fmt_dic = log_cfg_dic['formatters']['fmtgzyx_nocolor']

        logfile_handler = logging.FileHandler(log_path)

        fileformatter = logging.Formatter(**fmt_dic)

        logfile_handler.setFormatter(fileformatter)
        logfile_handler.setLevel('DEBUG')

        # the root logger
        # https://stackoverflow.com/questions/48712206/what-is-the-name-of-pythons-root-logger
        # the heritage for loggers
        # https://stackoverflow.com/questions/29069655/python-logging-with-a-common-logger-class-mixin-and-class-inheritance
        _logger.addHandler(logfile_handler)

        return logfile_handler

    def set_table_log(self,
                      out_dir=None,
                      step_suffix=''):
        if not out_dir:
            out_dir = self.tmp_dir

        ts = utils.get_timestamp()
        talo_name = "_".join((ts, step_suffix, "table.log"))
        talo_path = os.path.join(out_dir, talo_name)

        # initalize with a void table
        talo_df_void = pd.DataFrame([], columns=self.table.columns)
        talo_df_void.to_csv(talo_path, mode="w", index=False)

        # if self.table_log_path:
        self.table_log_path = talo_path

        return talo_path

    def write_in_table_log(self, row_in):
        pd.DataFrame(row_in).T.to_csv(self.table_log_path,
                                      mode='a',
                                      index=False,
                                      header=False)
        return None

    #  _______    _     _                                                                    _
    # |__   __|  | |   | |                                                                  | |
    #    | | __ _| |__ | | ___   _ __ ___   __ _ _ __   __ _  __ _  ___ _ __ ___   ___ _ __ | |_
    #    | |/ _` | '_ \| |/ _ \ | '_ ` _ \ / _` | '_ \ / _` |/ _` |/ _ \ '_ ` _ \ / _ \ '_ \| __|
    #    | | (_| | |_) | |  __/ | | | | | | (_| | | | | (_| | (_| |  __/ | | | | |  __/ | | | |_
    #    |_|\__,_|_.__/|_|\___| |_| |_| |_|\__,_|_| |_|\__,_|\__, |\___|_| |_| |_|\___|_| |_|\__|
    #                                                         __/ |
    #                                                        |___/

    def print_table(self,
                    no_print=False,
                    no_return=True,
                    max_colwidth=33):

        def _shrink_str(str_inp, maxlen=max_colwidth):
            if len(str_inp) <= maxlen:
                return str_inp
            else:
                halflen = int((maxlen / 2) - 1)
                str_out = str_inp[:halflen] + '..' + str_inp[-halflen:]
                return str_out

        form = dict()
        form['fraw'] = _shrink_str
        form['fpath_inp'] = _shrink_str
        form['fpath_out'] = _shrink_str

        form['epoch_srt'] = lambda t: t.strftime("%y-%m-%d %H:%M:%S")
        form['epoch_end'] = lambda t: t.strftime("%y-%m-%d %H:%M:%S")

        str_out = self.table.to_string(max_colwidth=max_colwidth + 1,
                                       formatters=form)
        # add +1 in max_colwidth for safety
        if not no_print:
            # print it in the logger (if silent , just return it)
            name = type(self).__name__
            logger.info("%s %s/%s\n%s", name,
                        self.site_id,
                        self.epoch_range,
                        str_out)
        if no_return:
            return None
        else:
            return str_out

    def load_table_from_filelist(self,
                                 input_files,
                                 inp_regex=".*",
                                 reset_table=True):
                                 #update_epoch_range=False):
        if reset_table:
            self._init_table(init_epoch=False)

        flist = input_list_reader(input_files,
                                  inp_regex)

        self.table['fpath_inp'] = flist
        self.table['fname'] = self.table['fpath_inp'].apply(os.path.basename)
        self.table['ok_inp'] = self.table['fpath_inp'].apply(os.path.isfile)

        #if update_epoch_range:
        #    self.update_epoch_range_from_table()

        return flist

    def load_table_from_prev_step_table(self,
                                        input_table,
                                        reset_table=True):
        if reset_table:
            self._init_table(init_epoch=False)

        self.table['fpath_inp'] = input_table['fpath_out'].values
        self.table['size_inp'] = input_table['size_out'].values
        self.table['fname'] = self.table['fpath_inp'].apply(os.path.basename)
        self.table['site'] = input_table['site'].values
        self.table['epoch_srt'] = input_table['epoch_srt'].values
        self.table['epoch_end'] = input_table['epoch_end'].values
        self.table['ok_inp'] = self.table['fpath_inp'].apply(os.path.isfile)

        return None

    def guess_local_rnx_files(self):

        local_paths_list = []

        for iepoch, epoch in self.table['epoch_srt'].items():
            # guess the potential local files
            local_dir_use = str(self.out_dir)
            #local_fname_use = str(self.remote_fname)

            epo_dt_srt = epoch.to_pydatetime()
            epo_dt_end = self.table.loc[iepoch, 'epoch_end'].to_pydatetime()
            prd_str = rinexmod.rinexfile.file_period_from_timedelta(epo_dt_srt, epo_dt_end)[0]

            local_fname_use = conv.statname_dt2rinexname_long(
                self.site_id9,
                epoch,
                country="XXX",
                data_source="R",  ### always will be with autorino
                file_period=prd_str,
                data_freq=self.session['data_frequency'],
                data_type="MO",
                format_compression='crx.gz',
                preset_type=None)

            local_path_use = os.path.join(local_dir_use,
                                          local_fname_use)

            local_path_use = self.translate_path(local_path_use,
                                                 epoch)

            local_fname_use = os.path.basename(local_path_use)

            local_paths_list.append(local_path_use)

            #iepoch = self.table[self.table['epoch_srt'] == epoch].index

            #self.table.loc[iepoch, 'fname'] = local_fname_use
            self.table.loc[iepoch, 'fpath_out'] = local_path_use
            logger.debug("local RINEX file guessed: %s", local_path_use)

        logger.info("nbr local RINEX files guessed: %s", len(local_paths_list))

        return local_paths_list

    def check_local_files(self):
        """
        check the existence of the local files, and set the corresponding
        booleans in the ok_out column
        """

        local_files_list = []

        for irow, row in self.table.iterrows():
            local_file = row['fpath_out']
            if os.path.exists(local_file) and os.path.getsize(local_file) > 0:
                self.table.loc[irow, 'ok_out'] = True
                self.table.loc[irow, 'size_out'] = os.path.getsize(local_file)
                local_files_list.append(local_file)
            else:
                self.table.loc[irow, 'ok_out'] = False

        return local_files_list

    def invalidate_small_local_files(self, threshold=.80):
        """
        if the local file is smaller than threshold * median 
        of the considered local files in the request table
        the ok_out boolean is set at False, and the local file 
        is redownloaded
        
        check_local_files must be launched 1st
        """

        med = self.table['size_out'].median(skipna=True)
        valid_bool = threshold * med < self.table['size_out']
        self.table.loc[:, 'ok_out'] = valid_bool
        invalid_local_files_list = list(self.table.loc[valid_bool, 'fpath_out'])

        return invalid_local_files_list

    def decompress_table_batch(self, table_col='fpath_inp',table_ok_col='ok_inp'):
        """
        decompress the potential compressed files in the ``table_col`` column
        and its corresponding ``table_ok_col`` boolean column
        (usually ``fpath_inp`` and ``ok_inp``)

        It will uncompress the file if it is a
        (gzip+)Hatanaka-compressed RINEX, or a generic-compressed file (gzip)

        It will create a new column ``fpath_ori`` (for original)
        to keep the trace of the original file

        This function process a complete table at once, and is faster than
        row-iterative ``decompress``
        """
        bool_comp = self.table[table_col].apply(arocmn.is_compressed)
        ### we also ensure the fact that the boolean ok column is True
        bool_ok = self.table[table_ok_col]
        bool_wrk = np.logical_and(bool_comp,bool_ok)
        idx_comp = self.table.loc[bool_wrk].index
        self.table.loc[idx_comp, 'fpath_ori'] = self.table.loc[idx_comp,
                                                               table_col]
        if hasattr(self, 'tmp_dir_unzipped'):
            tmp_dir = self.tmp_dir_unzipped
        else:
            tmp_dir = self.tmp_dir
        files_out = \
            self.table.loc[idx_comp, table_col].apply(arocmn.decompress,
                                                      args=(tmp_dir,))
        self.table.loc[idx_comp, table_col] = files_out
        self.table.loc[idx_comp, 'ok_inp'] = \
            self.table.loc[idx_comp, table_col].apply(os.path.isfile)
        self.table.loc[idx_comp, 'fname'] = \
            self.table.loc[idx_comp, table_col].apply(os.path.basename)

        return files_out

    def decompress(self, table_col='fpath_inp', table_ok_col='ok_inp'):
        """
        decompress the potential compressed files in the ``table_col`` column
        and its corresponding ``table_ok_col`` boolean column
        (usually ``fpath_inp`` and ``ok_inp``)

        It will uncompress the file if it is a
        (gzip+)Hatanaka-compressed RINEX, or a generic-compressed file
        (gzip only for the moment)

        It will create a new column ``fpath_ori`` (for original)
        to keep the trace of the original file
        """
        files_uncmp_list = []
        for irow, row in self.table.iterrows():
            file_uncmp = self.on_row_decompress(irow,table_col=table_col,table_ok_col=table_ok_col)
            files_uncmp_list.append(file_uncmp)

        return files_uncmp_list

    #  ______ _ _ _              _        _     _
    # |  ____(_) | |            | |      | |   | |
    # | |__   _| | |_ ___ _ __  | |_ __ _| |__ | | ___
    # |  __| | | | __/ _ \ '__| | __/ _` | '_ \| |/ _ \
    # | |    | | | ||  __/ |    | || (_| | |_) | |  __/
    # |_|    |_|_|\__\___|_|     \__\__,_|_.__/|_|\___|

    def filter_bad_keywords(self, keywords_path_excl):
        """
        Filter a list of raw files if the full path contains certain keywords

        modify the boolean "ok_inp" of the object's table
        returns the filtered raw files in a list
        """
        flist_out = []
        ok_inp_bool_stk = []
        nfil = 0
        for irow, row in self.table.iterrows():
            f = row['fname']
            boolbad = utils.patterns_in_string_checker(f, *keywords_path_excl)
            if boolbad:
                self.table.iloc[irow, 'ok_inp'] = False
                logger.debug("file filtered, contains an excluded keyword: %s",
                             f)
                nfil += 1
            else:
                if not row.ok_inp:  # ok_inp is already false
                    ok_inp_bool_stk.append(False)
                else:
                    ok_inp_bool_stk.append(True)
                    flist_out.append(f)

        # final replace of ok init
        self.table['ok_inp'] = ok_inp_bool_stk

        logger.info("%6i files filtered, their paths contain bad keywords",
                    nfil)
        return flist_out

    def filter_year_min_max(self,
                            year_min=1980,
                            year_max=2099,
                            year_in_inp_path=None):
        """
        Filter a list of raw files if they are not in a year range
        it is the year in the file path which is tested

        year_in_inp_path is the position of the year in the absolute path
        e.g.
        if the absolute path is:
        /home/user/input_data/raw/2011/176/PSA1201106250000a.T00
        year_in_inp_path is 4

        if no year_in_inp_path provided, a regex search is performed
        (more versatile, but less robust)


        year min and year max are included in the range

        modify the boolean "ok_inp" of the object's table
        returns the filtered raw files in a list
        """
        flist_out = []
        # nfil = 0

        ok_inp_bool_stk = []

        def _year_detect(fpath_inp, year_in_inp_path=None):
            try:
                if year_in_inp_path:
                    year_folder = int(fpath_inp.split("/")[year_in_inp_path])
                else:
                    rgx = re.search(r"\/(19|20)[0-9]{2}\/", fpath_inp)
                    year_folder = int(rgx.group()[1:-1])
                return year_folder
            except Exception:
                logger.warning("unable to get the year in path: %s",
                               fpath_inp)
                return np.nan

        years = self.table['fraw'].apply(
            _year_detect, args=(year_in_inp_path,))

        bool_out_range = (years < year_min) | (years > year_max)
        bool_in_range = np.logical_not(bool_out_range)

        #############################

        ok_inp_bool_stk = bool_in_range & self.table['ok_inp']
        nfil_total = sum(bool_out_range)
        # logical inhibition a.\overline{b}
        nfil_spec = sum(np.logical_and(bool_out_range, self.table['ok_inp']))

        # final replace of ok init
        self.table['ok_inp'] = ok_inp_bool_stk

        logger.info("%6i/%6i files filtered (total/specific) not in the year min/max range (%4i/%4i)",
                    nfil_total, nfil_spec, year_min, year_max)

        return flist_out

    def filter_filelist(self, filelist_exclu_inp,
                        message_manu_exclu=False):
        """
        Filter a list of raw files if they are present in a text file list
        e.g. an OK log or manual exclusion list

        modify the boolean "ok_inp" of the object's table
        returns the filtered raw files in a list
        """

        flist_exclu = input_list_reader(filelist_exclu_inp)

        flist_out = []
        ok_inp_bool_stk = []

        nfil = 0
        for irow, row in self.table.iterrows():
            f = row.fraw
            if f in flist_exclu:
                nfil += 1
                ok_inp_bool_stk.append(False)
                if not message_manu_exclu:
                    logger.debug(
                        "file filtered, was OK during a previous run (legacy simple list): %s", f)
                else:
                    logger.debug(
                        "file filtered manually in the exclusion list: %s", f)
            else:
                if not row.ok_inp:  # ok_inp is already false
                    ok_inp_bool_stk.append(False)
                else:
                    ok_inp_bool_stk.append(True)
                    flist_out.append(f)

        if not message_manu_exclu:
            logger.info(
                "%6i files filtered, were OK during a previous run (legacy simple OK list)", nfil)
        else:
            logger.info(
                "%6i files manually filtered in the exclusion list,", nfil)

        # final replace of ok init
        self.table['ok_inp'] = ok_inp_bool_stk

        return flist_out

    def filter_ok_out(self):
        """
        Filter a list of raw files if they have a positive ok_out boolean
        (i.e. the converted file exists already) 
        
        modify the boolean "ok_inp" of the object's table
        returns the filtered raw files in a list
        """

        def _not_impl(ok_inp, ok_out):
            """
            The truth table we want is this one
            ok_inp ok_out result
            0      0      0
            1      0      1
            0      1      0
            1      1      0
            
            it is the negation of an implication
            i.e. NOT(ok_inp => ok_out) i.e. ok_inp AND NOT(ok_out)
            """

            res = np.logical_and(ok_inp, np.logical_not(ok_out))
            return res

        ok_inp_new = _not_impl(self.table['ok_inp'].values,
                               self.table['ok_out'].values)

        flist_out = list(self.table['fpath_inp'][ok_inp_new])

        self.table['ok_inp'] = ok_inp_new

        return flist_out

    def filter_previous_tables(self,
                               df_prev_tab):
        """
        Filter a list of raw files if they are present in previous
        conversion tables stored as log

        modify the boolean "ok_inp" of the object's table
        returns the filtered raw files in a list
        """

        col_ok_names = ["ok_inp", "ok_conv", "ok_rnxmod"]

        # previous files when everthing was ok
        prev_bool_ok = df_prev_tab[col_ok_names].apply(np.logical_and.reduce,
                                                       axis=1)

        prev_files_ok = df_prev_tab[prev_bool_ok].fraw

        # current files which have been already OK and which have already
        # ok_inp == False
        # here the boolean value are inverted compared to the table:
        # True = skip me / False = keep me
        # a logical not inverts everything at the end
        curr_files_ok_prev = self.table['fraw'].isin(prev_files_ok)
        curr_files_off_already = np.logical_not(self.table['ok_inp'])

        curr_files_skip = np.logical_or(curr_files_ok_prev,
                                        curr_files_off_already)

        self.table['ok_inp'] = np.logical_not(curr_files_skip)

        logger.info("%6i files filtered, were OK during a previous run (table list)",
                    curr_files_ok_prev.sum())

        flist_out = list(self.table['fraw', self.table['ok_inp']])

        return flist_out

    def filter_purge(self, col='ok_inp', inplace=False):
        """
        filter the table according to a "ok" column
        i.e. remove all the values with a False values
        """

        if len(self.table) == 0:
            logger.warning("the table is empty, unable to purge it")
            out = pd.DataFrame([])
        elif inplace:
            self.table = self.table[self.table[col]]
            out = list(self.table[col])
        else:
            out = self.table[self.table[col]]
        return out

    #               _   _
    #     /\       | | (_)
    #    /  \   ___| |_ _  ___  _ __  ___    ___  _ __    _ __ _____      _____
    #   / /\ \ / __| __| |/ _ \| '_ \/ __|  / _ \| '_ \  | '__/ _ \ \ /\ / / __|
    #  / ____ \ (__| |_| | (_) | | | \__ \ | (_) | | | | | | | (_) \ V  V /\__ \
    # /_/    \_\___|\__|_|\___/|_| |_|___/  \___/|_| |_| |_|  \___/ \_/\_/ |___/
    #

    def on_row_convert(self, irow, out_dir_inp, converter_inp):
        self.table.loc[irow, 'ok_inp'] = True

        frnxtmp, _ = arocnv.converter_run(self.table.loc[irow, 'fpath_inp'],
                                          out_dir_inp,
                                          converter=converter_inp)
        if frnxtmp:
            ### update table if things go well
            self.table.loc[irow, 'fpath_out'] = frnxtmp
            epo_srt_ok, epo_end_ok = operational.rinex_start_end(frnxtmp)
            self.table.loc[irow, 'epoch_srt'] = epo_srt_ok
            self.table.loc[irow, 'epoch_end'] = epo_end_ok
            self.table.loc[irow, 'ok_out'] = True
        else:
            ### update table if things go wrong
            self.table.loc[irow, 'ok_out'] = False
        return frnxtmp

    def on_row_rinexmod(self, irow, out_dir_inp, rinexmod_kwargs):

        frnx = self.table.loc[irow, 'fpath_out']

        try:
            frnxmod = rinexmod.rinexmod_api.rinexmod(frnx,
                                                     out_dir_inp,
                                                     **rinexmod_kwargs)
            ### update table if things go well
            self.table.loc[irow, 'ok_out'] = True
            self.table.loc[irow, 'fpath_out'] = frnxmod
            self.table.loc[irow, 'size_out'] = os.path.getsize(frnxmod)
            self.write_in_table_log(self.table.loc[irow])

        except Exception as e:
            ### update table if things go wrong
            logger.error(e)
            self.table.loc[irow, 'ok_out'] = False
            self.write_in_table_log(self.table.loc[irow])
            frnxmod = None
            raise e

        return frnxmod

    def on_row_move_final(self, irow, out_dir_inp=None):

        if out_dir_inp:
            out_dir = out_dir_inp
        else:
            out_dir = self.out_dir

        ### def output folders
        outdir_use = self.translate_path(out_dir,
                                         epoch_inp=self.table.loc[irow,'epoch_srt'])

        frnxmod = self.table.loc[irow, 'fpath_out']

        try:
            ### do the move
            utils.create_dir(outdir_use)
            frnxfin = shutil.copy2(frnxmod, outdir_use)
            self.table.loc[irow, 'ok_out'] = True
            self.table.loc[irow, 'fpath_out'] = frnxfin
            self.table.loc[irow, 'size_out'] = os.path.getsize(frnxfin)
        except Exception as e:
            logger.error(e)
            self.table.loc[irow, 'ok_out'] = False
            self.write_in_table_log(self.table.loc[irow])
            frnxfin = None
            raise e

        return frnxfin

    def on_row_decompress(self,irow,tmp_dir_unzipped_inp=None,
                          table_col='fpath_inp', table_ok_col='ok_inp'):

        if tmp_dir_unzipped_inp:
            tmp_dir_unzipped = tmp_dir_unzipped_inp
        elif hasattr(self, 'tmp_dir_unzipped'):
            tmp_dir_unzipped = self.tmp_dir_unzipped
        else:
            tmp_dir_unzipped = self.tmp_dir


        bool_comp = arocmn.is_compressed(self.table.loc[irow, table_col])
        bool_ok = self.table.loc[irow,table_ok_col]
        bool_wrk = np.logical_and(bool_comp, bool_ok)

        if bool_wrk:
            if 'fpath_ori' not in self.table.columns:
                self.table['fpath_ori'] = [np.nan] * len(self.table)
            self.table.loc[irow, 'fpath_ori'] = self.table.loc[irow,table_col]

        file_uncomp_out = arocmn.decompress_file(self.table.loc[irow, table_col],
                                                 tmp_dir_unzipped)

        self.table.loc[irow, table_col] = file_uncomp_out
        self.table.loc[irow, 'ok_inp'] = os.path.isfile(self.table.loc[irow, table_col])
        self.table.loc[irow, 'fname'] = os.path.basename(self.table.loc[irow, table_col])

        return file_uncomp_out


#  __  __ _               __                  _   _
# |  \/  (_)             / _|                | | (_)
# | \  / |_ ___  ___    | |_ _   _ _ __   ___| |_ _  ___  _ __  ___
# | |\/| | / __|/ __|   |  _| | | | '_ \ / __| __| |/ _ \| '_ \/ __|
# | |  | | \__ \ (__ _  | | | |_| | | | | (__| |_| | (_) | | | \__ \
# |_|  |_|_|___/\___(_) |_|  \__,_|_| |_|\___|\__|_|\___/|_| |_|___/


def create_dummy_site_dic():
    d = dict()

    d['name'] = 'XXXX'
    d['site_id'] = 'XXXX00XXX'
    d['domes'] = '00000X000'
    d['sitelog_path'] = '/null'
    d['position_xyz'] = (6378000, 0, 0)

    return d


def create_dummy_session_dic():
    d = dict()

    d['name'] = 'NA'
    d['data_frequency'] = "30S"
    d['tmp_dir_parent'] = '<$HOME>/autorino_workflow_tests/tmp'
    d['tmp_dir_structure'] = '<site_id9>/%Y/%j'
    d['log_parent_dir'] = '<$HOME>/autorino_workflow_tests/log'
    d['log_dir_structure'] = '<site_id9>/%Y/%j'
    d['out_dir_parent'] = '<$HOME>/autorino_workflow_tests/out'
    d['out_dir_structure'] = '<site_id9>/%Y/%j'

    return d


def input_list_reader(inp_fil, inp_regex=".*"):
    """
    Handles mutiples types of input lists (in a general sense)
    and returns a python list of the input

    inp_fil can be:
        * a python list (then nothing is done)
        * a text file path containing a list of files (readed as a python list)
        * a tuple containing several text files path  (recursive version of the previous point)
        * a directory path (all the files matching inp_regex are readed)
    """

    if not inp_fil:
        flist = []
    elif isinstance(inp_fil, tuple) and os.path.isfile(inp_fil[0]):
        flist = list(np.hstack([open(f, "r+").readlines() for f in inp_fil]))
        flist = [f.strip() for f in flist]
    elif isinstance(inp_fil, list):
        flist = inp_fil
    elif os.path.isfile(inp_fil):
        flist = open(inp_fil, "r+").readlines()
        flist = [f.strip() for f in flist]
    elif os.path.isdir(inp_fil):
        flist = utils.find_recursive(inp_fil,
                                     inp_regex,
                                     case_sensitive=False)
    else:
        flist = []
        logger.warning("the filelist is empty")

    if inp_regex != ".*":
        flist = [f for f in flist if re.match(inp_regex, f)]

    return flist
