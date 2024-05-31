#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 30/05/2024 16:22:55

@author: psakic
"""


import argparse
import autorino.common as arocmn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert RAW files to RINEX.')
    parser.add_argument('raws_inp', nargs='+', help='The input RAW files to be converted')
    parser.add_argument('out_dir', help='The output directory where the converted files will be stored')
    parser.add_argument('--out_dir_structure', help="""The structure of the output directory. 
    If provided, the converted files will be stored in a subdirectory of out_dir following this structure.
    Default value is '<SITE_ID4>/%%Y/'.""")
    parser.add_argument('--tmp_dir', help='The temporary directory used during the conversion process')
    parser.add_argument('--log_dir', help='The directory where logs will be stored. If not provided, it defaults to tmp_dir')
    parser.add_argument('--rinexmod_options', type=dict, help='The options for modifying the RINEX files during the conversion')
    parser.add_argument('--metadata', help='''The metadata to be included in the converted RINEX files. \n Possible inputs are: \n 
         * list of string (sitelog file paths), 
         * single string (single sitelog file path),
         * single string (directory containing the sitelogs),
         * list of MetaData objects,
         * single MetaData object''')
    parser.add_argument('--force', action='store_true', help='Force the conversion even if the output files already exist')

    args = parser.parse_args()

    arocmn.convert_rnx(args.raws_inp, args.out_dir, args.tmp_dir, args.log_dir, args.out_dir_structure, args.rinexmod_options, args.metadata, args.force)
