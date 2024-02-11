#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 11 18:44:52 2024

@author: psakicki
"""

import argparse
import autorino.config as arocfg


if __name__ == '__main__':

    ##### Parsing Args
    parser = argparse.ArgumentParser(description='Assisted Unloading, Treatment and Organization of RINEX observations')
    
    parser.add_argument('-c', '--config', type=str,
                        help='config file path or directory path containing the config file', default='')
    parser.add_argument('-s', '--start', type=str,
                        help='', default='')
    parser.add_argument('-e', '--end', type=str,
                        help='', default='')
    parser.add_argument('-l', '--list_sites', type=str,
                        help='', default='')
    
    
    args = parser.parse_args()

    config = args.config
    start = args.start
    end = args.end
    list_sites = args.list_sites

    arocfg.autorino_run(config)
    
    
