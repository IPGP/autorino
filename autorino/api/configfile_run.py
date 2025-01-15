#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 18/09/2024 18:23:30

@author: psakic
"""

import glob
import os
import autorino.cfgfiles as arocfg
import autorino.common as arocmn

#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger('autorino')
logger.setLevel(aroenv.aro_env_dict["general"]["log_level"])


def cfgfile_run(
    cfg_in,
    main_cfg_in,
    sites_list=None,
    epo_srt=None,
    epo_end=None,
    period="1D",
    steps_select_list=None,
    exclude_steps_select=False,
    force=False,
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
    epo_srt : str, list, optional
        The start date for the epoch range.
        Can be a list; if so, each epoch is considered separately.
        Can be a file path; if so, the file contains a list of start epochs
        Default is None.
    epo_end : str, optional
        The end date for the epoch range. Default is None.
    period : str, optional
        The period for the epoch range. Default is "1D".
    steps_select_list : list, optional
        A list of selected steps to be executed.
        If not provided, all steps in 'steps_lis' will be executed.
        Default is None.
    exclude_steps_select : bool, optional
        If True the selected steps indicated in step_select_list are excluded.
        It is the opposite behavior of the regular one using steps_select_list
        Default is False.
    force : bool, optional
        If True, the steps will be executed even if the output files already exist.
        overrides the 'force' parameters in the configuration file.
        Default is False.

    Raises
    ------
    Exception
        If the provided cfg_in does not exist as a file or directory, an exception is raised.

    Returns
    -------
    None
    """

    # Check if cfg_in is a directory or a file and get the list of configuration files
    if os.path.isdir(cfg_in):
        cfg_use_lis = list(sorted(glob.glob(cfg_in + "/*yml")))
    elif os.path.isfile(cfg_in):
        cfg_use_lis = [cfg_in]
    else:
        logger.error("%s does not exist, check input cfgfiles file/dir", cfg_in)
        raise Exception

    # Determine the epoch range based on the provided start and end dates
    if epo_srt and epo_end:
        epoch_range = arocmn.EpochRange(epo_srt, epo_end, period)
    elif epo_srt and not epo_end:
        if os.path.isfile(epo_srt):
            with open(epo_srt, "r") as f:
                start_use = f.read().splitlines()
        elif isinstance(epo_srt, list):
            start_use = epo_srt
        else:
            logger.critical("start must be a list or a file path")
            raise Exception
        epoch_range = arocmn.EpochRange(start_use, period=period)
    else:
        epoch_range = None

    # Process each configuration file
    for cfg_use in cfg_use_lis:
        if sites_list:
            # Quick load to check if the site is in the list or not
            y_quick = arocfg.load_cfg(configfile_path=cfg_use)
            site_quick = y_quick["station"]["site"]["site_id"]
            if site_quick not in sites_list:
                logger.info("Skipping site %s (not in sites list)", site_quick)
                continue

        # Read the configuration and run the steps
        # step_lis_lis is a list of list because you can have several sessions in the same configuration file
        steps_lis_lis, steps_dic_dic, y_station = arocfg.read_cfg(
            configfile_path=cfg_use, main_cfg_path=main_cfg_in, epoch_range=epoch_range
        )

        for steps_lis in steps_lis_lis:
            arocfg.run_steps(
                steps_lis,
                steps_select_list=steps_select_list,
                exclude_steps_select=exclude_steps_select,
                force=force,
            )

    return None
