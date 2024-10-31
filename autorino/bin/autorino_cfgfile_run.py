#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 11 18:44:52 2024

@author: psakic
"""

import argparse
import autorino.api as aroapi

def main():
    ##### Parsing Args
    parser = argparse.ArgumentParser(description='Assisted Unloading, Treatment and Organization of RINEX observations')

    parser.add_argument('-c', '--config', type=str,
                        help='cfgfiles file path or directory path containing the cfgfiles file', default='')
    parser.add_argument('-m', '--main_config', type=str,
                        help='main cfgfiles file path', default='')
    parser.add_argument('-s', '--start', type=str,
                        help='', default=None)
    parser.add_argument('-e', '--end', type=str,
                        help='', default=None)
    parser.add_argument('-p', '--period', type=str,
                        help='', default='1D')
    parser.add_argument('-ls', '--list_sites', type=str,
                        help='Comma-separated list of site identifiers', default='')
    parser.add_argument('-ss', '--steps_select_list', type=str,
                        help='Comma-separated list of selected steps to be executed', default='')
    parser.add_argument('-es', '--exclude_steps_select', action='store_true',
                        help='Flag to exclude the selected steps', default=False)
    parser.add_argument('-f', '--force', action='store_true',
                        help='force the execution of the steps', default=False)

    args = parser.parse_args()

    config = args.config
    main_config = args.main_config
    start = args.start
    end = args.end
    period = args.period
    list_sites = args.list_sites.split(',') if args.list_sites else None
    steps_select_list = args.steps_select_list.split(',') if args.steps_select_list else None
    exclude_steps_select = args.exclude_steps_select
    force = args.force

    aroapi.cfgfile_run(cfg_in=config,
                       main_cfg_in=main_config,
                       sites_list=list_sites,
                       epo_srt=start,
                       epo_end=end,
                       period=period,
                       steps_select_list=steps_select_list,
                       exclude_steps_select=exclude_steps_select,
                       force=force)

if __name__ == '__main__':
    main()

