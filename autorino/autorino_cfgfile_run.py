#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 11 18:44:52 2024

@author: psakic
"""

import argparse
import autorino.common as arocmn

if __name__ == '__main__':
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

    args = parser.parse_args()

    config = args.config
    main_config = args.main_config
    start = args.start
    end = args.end
    period = args.period
    list_sites = args.list_sites.split(',') if args.list_sites else None

    arocmn.autorino_cfgfile_run(cfg_in=config,
                                main_cfg_in=main_config,
                                sites_list=list_sites,
                                epo_srt=start,
                                epo_end=end,
                                period=period)
