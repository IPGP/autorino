#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 25/10/2025 16:09:59

@author: psakic
"""

import argparse
import yaml
from autorino.api.splice_rnx_rel import splice_rnx_rel


def main():
    parser = argparse.ArgumentParser(description=splice_rnx_rel.__doc__)
    parser.add_argument(
        "-i", "--rnxs_inp",
        required=True,
        nargs="+",
        help="The input RINEX files to be spliced. The input can be a list, a text file path, a tuple of text files or a directory path."
    )
    parser.add_argument(
        "-o", "--out_dir",
        required=True,
        help="The output directory where the spliced files will be stored."
    )
    parser.add_argument(
        "-t", "--tmp_dir",
        required=True,
        help="The temporary directory used during the splicing process."
    )
    parser.add_argument(
        "-l", "--log_dir",
        default=None,
        help="The directory where logs will be stored. (optional)"
    )
    parser.add_argument(
        "-S", "--handle_software",
        default="converto",
        help="The software to be used for handling the RINEX files during the splice operation. Defaults to 'converto'. (optional)"
    )
    parser.add_argument(
        "-p", "--period",
        default="1d",
        help="The period for splicing the RINEX files. Defaults to '1d'. (optional)"
    )
    parser.add_argument(
        "-R", "--rolling_period",
        action="store_true",
        help="Whether to use a rolling period for splicing the RINEX files. (optional)"
    )
    parser.add_argument(
        "-r", "--rolling_ref",
        default="-1",
        help="The reference for the rolling period (datetime-like or int). Use -1 for the last epoch. (optional)"
    )
    parser.add_argument(
        "-m", "--round_method",
        default="floor",
        help="The method for rounding the epochs during the splice operation. Defaults to 'floor'. (optional)"
    )
    parser.add_argument(
        "-d", "--drop_epoch_rnd",
        action="store_true",
        help="Whether to drop the rounded epochs during the splice operation. (optional)"
    )
    parser.add_argument(
        "-x", "--rinexmod_options",
        type=yaml.safe_load,
        default=None,
        help="Options for modifying the RINEX files, provided as a YAML/JSON string or file content (e.g. '{longname: False}'). (optional)"
    )
    parser.add_argument(
        "-M", "--metadata",
        nargs="+",
        default=None,
        help="Metadata to include (list of sitelog paths, single sitelog path, directory, or MetaData objects). (optional)"
    )

    args = parser.parse_args()

    rolling_ref_val = args.rolling_ref

    spc_main_obj = splice_rnx_rel(
        rnxs_inp=args.rnxs_inp,
        out_dir=args.out_dir,
        tmp_dir=args.tmp_dir,
        log_dir=args.log_dir,
        handle_software=args.handle_software,
        period=args.period,
        rolling_period=args.rolling_period,
        rolling_ref=rolling_ref_val,
        round_method=args.round_method,
        drop_epoch_rnd=args.drop_epoch_rnd,
        rinexmod_options=args.rinexmod_options,
        metadata=args.metadata,
    )

    # Optionally print a short summary or representation
    if spc_main_obj is not None:
        print(spc_main_obj)

if __name__ == "__main__":
    main()