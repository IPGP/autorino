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

logger = logging.getLogger("autorino")
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])


def cfgfile_run(
    cfg_in,
    incl_cfg_in,
    sites_list=None,
    exclude_sites=False,
    epo_srt=None,
    epo_end=None,
    period="1D",
    steps_list=None,
    exclude_steps=False,
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
    incl_cfg_in : str or list of str
        The include configuration files to be used for development/advanced purposes.
        If a list is provided, all files in the list will be included.
        It will override the `include` section of the `cfg_in` configuration file.
    sites_list : list, optional
        A list of site identifiers to filter the configuration files.
         If provided, only configurations for sites in this list will be processed.
         Default is None.
    exclude_sites : bool, optional
        If True, the site in sites_list will be ignored.
        It is the opposed behavior of the regular one using sites_list.
        Default is False.
    epo_srt : str, list, optional
        The start date for the epoch range.
        Can be a list; if so, each epoch is considered separately.
        Can be a file path; if so, the file contains a list of start epochs
        The epoch can be formatted as:
        * a litteral, e.g. 'yesterday', '10 days ago'
        * YYYY-DDD, year-day of year, e.g. 2025-140
        * YYYY-MM-DD, classic calendar date, e.g. 2025-05-20
        Default is None.
    epo_end : str, optional
        The end date for the epoch range. Default is None.
    period : str, optional
        The period for the epoch range. Default is "1D".
    steps_list : list, optional
        A list of selected steps to be executed.
        If not provided, all steps in 'steps_lis' will be executed.
        Default is None.
    exclude_steps : bool, optional
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
    exit_code_max : int
        The maximum exit code from all steps executed in the configuration files.
        If no steps were executed, returns 0.
    """

    # Check if cfg_in is a directory or a file and get the list of configuration files
    if os.path.isdir(cfg_in):
        cfg_use_lis = []
        for ext in ("/*yml", "/*yaml"):
            cfg_use_lis.extend(list(sorted(glob.glob(cfg_in + ext))))
    elif os.path.isfile(cfg_in):
        cfg_use_lis = [cfg_in]
    else:
        logger.error("%s does not exist, check input cfgfiles file/dir", cfg_in)
        return None

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
            return None
        epoch_range = arocmn.EpochRange(start_use, period=period)
    else:
        epoch_range = None

    # Process each configuration file
    for cfg_use in cfg_use_lis:
        if sites_list:
            # Quick load to check if the site is in the list or not
            y_quick = arocfg.load_cfg(cfg_path=cfg_use)
            site_quick = y_quick["station"]["site"]["site_id"]
            ### case 1: sites_list are the sites we want
            if not exclude_sites and (site_quick not in sites_list):
                logger.info("Skipping site %s (not in sites list)", site_quick)
                continue
            ### case 2: sites_list are the sites we ignore
            elif exclude_sites and (site_quick in sites_list):
                logger.info("Skipping site %s (in ignored sites list)", site_quick)
                continue
            ### case 3: regular case
            else:
                pass

        # Read the configuration and run the steps
        # step_lis_lis is a list of list because you can have several sessions in the same configuration file
        steps_lis_lis, steps_dic_dic, y_use = arocfg.read_cfg(
            site_cfg_path=cfg_use,
            include_cfg_paths_xtra=incl_cfg_in,
            epoch_range=epoch_range,
        )

        for steps_lis in steps_lis_lis:
            arocfg.run_steps(
                steps_lis,
                steps_select_list=steps_list,
                exclude_steps_select=exclude_steps,
                force=force,
            )

    # Get the maximum exit code from all steps
    exit_code_max = max(
        [max([stp.exit_code for stp in steps_lis]) for steps_lis in steps_lis_lis]
    )

    return exit_code_max
