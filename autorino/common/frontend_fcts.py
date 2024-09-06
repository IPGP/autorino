#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 23/04/2024 14:21:56

@author: psakic
"""

import glob
import os

import autorino.cfgfiles as arocfg
import autorino.download as arodwl
import autorino.convert as arocnv
import autorino.handle as arohdl
import autorino.common as arocmn

#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger(__name__)
logger.setLevel(aroenv.aro_env_dict["general"]["log_level"])


def autorino_cfgfile_run(
    cfg_in, main_cfg_in, sites_list=None, start=None, end=None, period="1D",
):
    """
    Run the Autorino configuration files.

    This function takes in a configuration file or a directory of configuration files,
    reads the configuration, and runs the steps specified in the configuration.

    Parameters
    ----------
    cfg_in : str
        The input configuration file or directory of configuration files.
        If a directory is provided, all files ending with '.yml' will be used.
    main_cfg_in : str
        The main configuration file to be used.
    sites_list : list, optional
        A list of site identifiers to filter the configuration files.
         If provided, only configurations for sites in this list will be processed. Default is None.
    start : str, list, optional
        The start date for the epoch range. Default is None.
        if it is a file path, the file contains a list of start epochs
    end : str, optional
        The end date for the epoch range. Default is None.
    period : str, optional
        The period for the epoch range. Default is "1D".

    Raises
    ------
    Exception
        If the provided cfg_in does not exist as a file or directory, an exception is raised.

    Returns
    -------
    None
    """
    if os.path.isdir(cfg_in):
        cfg_use_lis = glob.glob(cfg_in + "/*yml")
    elif os.path.isfile(cfg_in):
        cfg_use_lis = [cfg_in]
    else:
        logger.error("%s does not exist, check input cfgfiles file/dir", cfg_in)
        raise Exception

    if start and end:
        epoch_range = arocmn.EpochRange(start, end, period)
    if start and not end:
        if os.path.isfile(start):
            with open(start, "r") as f:
                start_use = f.read().splitlines()
        elif isinstance(start, list):
            start_use = start
        else:
            logger.critical("start must be a list or a file path")
            raise Exception
        epoch_range = arocmn.EpochRange(start_use, period=period)
    else:
        epoch_range = None

    for cfg_use in cfg_use_lis:
        if sites_list:
            # quick load to check if the site is in the list or not
            y_quick = arocfg.load_cfg(configfile_path=cfg_use)
            site_quick = y_quick["station"]["site"]["site_id"]
            if site_quick not in sites_list:
                logger.info("Skipping site %s (not in sites list)", site_quick)
                continue

        steps_lis_lis, steps_dic_dic, y_station = arocfg.read_cfg(
            configfile_path=cfg_use, main_cfg_path=main_cfg_in, epoch_range=epoch_range
        )

        for steps_lis in steps_lis_lis:
            arocfg.run_steps(steps_lis)

    return None


def download_raw(
    epoch_range,
    out_dir,
    hostname,
    inp_dir,
    inp_structure,
    site_id="XXXX00XXX",
    login="",
    password="",
    tmp_dir=None,
    log_dir=None,
    options=dict(),
    session=dict(),
):
    """
    Downloads raw GNSS data files.

    This function downloads raw GNSS data files for a specified epoch range and stores them
    in the specified output directory.

    Parameters
    ----------
    epoch_range : object
        The epoch range for which the data files are to be downloaded.
    out_dir : str
        The output directory where the downloaded files will be stored.
    hostname : str
        The hostname of the server from which the data files will be downloaded.
    inp_dir : str
        The parent directory on the server where the data files are located.
    inp_structure : str
        The structure of the input directory on the server.
    site_id : str, optional
        The site identifier for the data files. Default is "XXXX00XXX".
    login : str, optional
        The login username for the server. Default is an empty string.
    password : str, optional
        The login password for the server. Default is an empty string.
    tmp_dir : str, optional
        The temporary directory used during the download process. Default is None.
    log_dir : str, optional
        The directory where logs will be stored. If not provided, it defaults to tmp_dir. Default is None.
    options : dict, optional
        Additional options for the download process. Default is an empty dictionary.
    session : dict, optional
        Session information for the download process. Default is an empty dictionary.

    Returns
    -------
    object
        The DownloadGnss object after the download operation.
    """
    access_dic = dict()
    access_dic["hostname"] = hostname
    access_dic["login"] = login
    access_dic["password"] = password

    site_dic = dict()
    site_dic["site_id"] = site_id

    dwl = arodwl.DownloadGnss(
        out_dir=out_dir,
        tmp_dir=tmp_dir,
        log_dir=log_dir,
        epoch_range=epoch_range,
        access=access_dic,
        #inp_dir_parent=inp_dir,
        #inp_structure=inp_structure,
        site=site_dic,
        session=session,
        options=options,
    )

    dwl.download()

    return dwl


def convert_rnx(
    raws_inp,
    out_dir,
    tmp_dir=None,
    log_dir=None,
    out_structure="<SITE_ID4>/%Y/",
    rinexmod_options=None,
    metadata=None,
    force=False,
):
    """
    Frontend function that performs RAW > RINEX conversion.

    Parameters
    ----------
    raws_inp : list
        The input RAW files to be converted.
        The input can be:
        * a python list
        * a text file path containing a list of files
        * a tuple containing several text files path
        * a directory path.
    out_dir : str
        The output directory where the converted files will be stored.
    tmp_dir : str, optional
        The temporary directory used during the conversion process.
        If not provided, it defaults to <out_dir>/tmp_convert_rnx.
        Defaults to None.
    log_dir : str, optional
        The directory where logs will be stored. If not provided, it defaults to tmp_dir.
         Defaults to None.
    out_structure : str, optional
        The structure of the output directory.
        If provided, the converted files will be stored in a subdirectory of out_dir following this structure.
        See README.md for more information. Typical values are '<SITE_ID4>/%Y/' or '%Y/%j/'.
        Default value is '<SITE_ID4>/%Y/'.
    rinexmod_options : dict, optional
        The options for modifying the RINEX files during the conversion. Defaults to None.
    metadata : str or list, optional
        The metadata to be included in the converted RINEX files. Possible inputs are:
         * list of string (sitelog file paths),
         * single string (single sitelog file path)
         * single string (directory containing the sitelogs)
         * list of MetaData objects
         * single MetaData object.
         Defaults to None.
    force : bool, optional
        If set to True, the conversion will be forced even if the output files already exist.
        Defaults to False.

    Returns
    -------
    None
    """
    if not tmp_dir:
        tmp_dir = os.path.join(out_dir, "tmp_convert_rnx")

    if not log_dir:
        log_dir = tmp_dir

    if out_structure:
        out_dir_use = os.path.join(out_dir, out_structure)
    else:
        out_dir_use = out_dir

    raws_use = raws_inp

    cnv = arocnv.ConvertGnss(out_dir_use, tmp_dir, log_dir, metadata=metadata)
    cnv.load_table_from_filelist(raws_use)

    cnv.convert(force=force, rinexmod_options=rinexmod_options)

    return cnv

def split_rnx(
    rnxs_inp,
    epoch_srt,
    epoch_end,
    period,
    out_dir,
    tmp_dir,
    log_dir=None,
    handle_software="converto",
    rinexmod_options=None,
    metadata=None,
):
    """
    Frontend function to split RINEX files based on certain criteria

    Parameters
    ----------
    rnxs_inp : list
        The input RINEX files to be split
        The input can be:
        * a python list
        * a text file path containing a list of files
        * a tuple containing several text files path
        * a directory path.
    epoch_srt : datetime-like
        The start epoch for the splicing operation.
    epoch_end : datetime-like
        The end epoch for the splicing operation.
    period : str
        The period for the splicing operation.
    out_dir : str
        The output directory where the split files will be stored
    tmp_dir : str
        The temporary directory used during the splitting process
    log_dir : str, optional
        The directory where logs will be stored. If not provided, it defaults to tmp_dir
    handle_software : str, optional
        The software to be used for handling the RINEX files during the split operation
    rinexmod_options : dict, optional
        The options for modifying the RINEX files during the split operation
    metadata : str or list, optional
        The metadata to be included in the split RINEX files
        Possible inputs are:
         * list of string (sitelog file paths),
         * single string (single sitelog file path)
         * single string (directory containing the sitelogs)
         * list of MetaData objects
         * single MetaData object

    Returns
    -------
    None
    """
    if not log_dir:
        log_dir = tmp_dir

    epo_rng = arocmn.EpochRange(epoch_srt, epoch_end, period)

    spt = arohdl.SplitGnss(out_dir, tmp_dir, log_dir,
                           epoch_range=epo_rng, metadata=metadata)

    spt.split(
        input_mode="given",
        input_rinexs=rnxs_inp,
        handle_software=handle_software,
        rinexmod_options=rinexmod_options,
        verbose=True
    )

    return spt


def splice_rnx_abs(
    rnxs_inp,
    epoch_srt,
    epoch_end,
    period,
    out_dir,
    tmp_dir,
    log_dir=None,
    handle_software="converto",
    rinexmod_options=None,
    metadata=None,
):
    """
    Splice RINEX files together in an absolute way, based on the provided epoch range.

    This function takes in a list of RINEX files and splices them together based on the specified
    epoch range and other criteria. The spliced files are stored in the specified output directory.

    Parameters
    ----------
    rnxs_inp : list
        The input RINEX files to be spliced.
    epoch_srt : str
        The start epoch for the splicing operation.
    epoch_end : str
        The end epoch for the splicing operation.
    period : str
        The period for the splicing operation.
    out_dir : str
        The output directory where the spliced files will be stored.
    tmp_dir : str
        The temporary directory used during the splicing process.
    log_dir : str, optional
        The directory where logs will be stored. If not provided, it defaults to tmp_dir.
    handle_software : str, optional
        The software to be used for handling the RINEX files during the splice operation. Defaults to "converto".
    rinexmod_options : dict, optional
        The options for modifying the RINEX files during the splice operation. Defaults to None.
    metadata : str or list, optional
        The metadata to be included in the spliced RINEX files. Possible inputs are:
         * list of string (sitelog file paths),
         * single string (single sitelog file path),
         * single string (directory containing the sitelogs),
         * list of MetaData objects,
         * single MetaData object. Defaults to None.

    Returns
    -------
    object
        The SpliceGnss object after the splice operation.
    """
    if not log_dir:
        log_dir = tmp_dir

    epo_rng = arocmn.EpochRange(epoch_srt, epoch_end, period)

    spc = arohdl.SpliceGnss(
        out_dir, tmp_dir, log_dir, epoch_range=epo_rng, metadata=metadata
    )

    spc.splice(
        input_mode="given",
        input_rinexs=rnxs_inp,
        handle_software=handle_software,
        rinexmod_options=rinexmod_options,
    )

    return spc


def splice_rnx_rel(
    rnxs_inp,
    out_dir,
    tmp_dir,
    log_dir=None,
    handle_software="converto",
    period="1d",
    rolling_period=False,
    rolling_ref=-1,
    round_method="floor",
    drop_epoch_rnd=False,
    rinexmod_options=None,
    metadata=None,
):
    """
    Splices RINEX files together in a relative way, based on certain criteria.

    This function takes in a list of RINEX files and splices them together based on the provided criteria.
    The spliced files are stored in the specified output directory.

    Parameters
    ----------
    rnxs_inp : list
        The input RINEX files to be spliced.
        The input can be:
        * a python list
        * a text file path containing a list of files
        * a tuple containing several text files path
        * a directory path.
    out_dir : str
        The output directory where the spliced files will be stored.
    tmp_dir : str
        The temporary directory used during the splicing process.
    log_dir : str, optional
        The directory where logs will be stored. If not provided, it defaults to tmp_dir.
    handle_software : str, optional
        The software to be used for handling the RINEX files during the splice operation.
        Defaults to "converto".
    period : str, optional
        The period for splicing the RINEX files. Defaults to "1d".
    rolling_period : bool, optional
        Whether to use a rolling period for splicing the RINEX files.
        If False, the spliced files will be based only on the "full" period provided,
        i.e. Day1 00h-24h, Day2 00h-24h, etc.
        If True, the spliced files will be based on the rolling period.
        i.e. Day1 00h-Day2 00h, Day1 01h-Day2 01h, Day1 02h-Day2 02h etc.
        Defaults to False.
        see also eporng_fcts.round_epochs function
    rolling_ref :  datetime-like or int, optional
        The reference for the rolling period.
        If datetime-like object, use this epoch as reference.
        If integer, use the epoch of the corresponding index
        Use -1 for the last epoch for instance.
        The default is -1.
        see also eporng_fcts.round_epochs function
    round_method : str, optional
        The method for rounding the epochs during the splice operation. Defaults to "floor".
    drop_epoch_rnd : bool, optional
        Whether to drop the rounded epochs during the splice operation. Defaults to False.
    rinexmod_options : dict, optional
        The options for modifying the RINEX files during the splice operation. Defaults to None.
    metadata : str or list, optional
        The metadata to be included in the spliced RINEX files. Possible inputs are:
         * list of string (sitelog file paths),
         * single string (single sitelog file path)
         * single string (directory containing the sitelogs)
         * list of MetaData objects
         * single MetaData object. Defaults to None.

    Returns
    -------
    spc_main_obj : object
        The main SpliceGnss object after the splice operation.
    """
    if not log_dir:
        log_dir = tmp_dir

    spc_inp = arohdl.SpliceGnss(out_dir, tmp_dir, log_dir, metadata=metadata)
    spc_inp.load_table_from_filelist(rnxs_inp)
    spc_inp.updt_epotab_rnx(use_rnx_filename_only=True)

    spc_main_obj, spc_objs_lis = spc_inp.group_by_epochs(
        period=period,
        rolling_period=rolling_period,
        rolling_ref=rolling_ref,
        round_method=round_method,
        drop_epoch_rnd=drop_epoch_rnd,
    )

    spc_main_obj.splice_core(
        handle_software=handle_software, rinexmod_options=rinexmod_options
    )

    return spc_main_obj
