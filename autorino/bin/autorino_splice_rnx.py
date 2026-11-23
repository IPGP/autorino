#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 17/04/2026

@author: psakic
"""

import argparse
import yaml
from autorino.api.splice_rnx import splice_rnx
from autorino.common.cli_fcts import prep_inputs


def main():
    desc = splice_rnx.__doc__.split("Parameters")[0]
    parser = argparse.ArgumentParser(
        description=desc, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # ------------------------------------------------------------------ #
    #  Common arguments                                                    #
    # ------------------------------------------------------------------ #
    parser.add_argument(
        "-i",
        "--rnxs_inp",
        required=True,
        nargs="+",
        help="Input RINEX files to be spliced. Can be a list of files, a text file path, "
        "a tuple of text file paths, or a directory path.",
    )
    parser.add_argument(
        "-o",
        "--out_dir",
        required=True,
        help="Output directory where the spliced files will be stored.",
    )
    parser.add_argument(
        "-t",
        "--tmp_dir",
        required=True,
        help="Temporary directory used during the splicing process.",
    )
    parser.add_argument(
        "-l",
        "--log_dir",
        default=None,
        help="Directory where logs will be stored. Defaults to tmp_dir. (optional)",
    )
    parser.add_argument(
        "-p",
        "--period",
        default="1d",
        help="Period for splicing the RINEX files. Defaults to '1d'. (optional)",
    )
    parser.add_argument(
        "-hs",
        "--handle_software",
        default="converto",
        help="Software used for handling the RINEX files. Defaults to 'converto'. (optional)",
    )
    parser.add_argument(
        "-rimo",
        "--rinexmod_options",
        type=yaml.safe_load,
        default=None,
        help="Options for modifying the RINEX files, provided as a YAML/JSON string "
        "(e.g. '{longname: False}'). (optional)",
    )
    parser.add_argument(
        "-m",
        "--metadata",
        nargs="+",
        default=None,
        help="Metadata to include: list of sitelog paths, single sitelog path, "
        "directory containing sitelogs, or MetaData objects. (optional)",
    )

    # ------------------------------------------------------------------ #
    #  Absolute mode arguments                                             #
    # ------------------------------------------------------------------ #
    abs_grp = parser.add_argument_group(
        "Absolute mode",
        "Arguments for absolute mode (used when --epoch_srt and --epoch_end are provided).",
    )
    abs_grp.add_argument(
        "-s",
        "--epoch_srt",
        default=None,
        help="Start epoch for the splicing operation (absolute mode). "
        "If omitted, relative mode is used. (optional)",
    )
    abs_grp.add_argument(
        "-e",
        "--epoch_end",
        default=None,
        help="End epoch for the splicing operation (absolute mode). "
        "If omitted, relative mode is used. (optional)",
    )

    abs_grp.add_argument(
        "-si",
        "--site",
        nargs="+",
        default=None,
        help="Site name(s) for the spliced RINEX files. "
        "One or more site names can be provided. "
        "Recommended to detect existing files to skip. (optional)",
    )

    abs_grp.add_argument(
        "-df",
        "--data_frequency",
        default="30S",
        help="Data frequency for the spliced RINEX files. Defaults to '30S'. (optional)",
    )

    # ------------------------------------------------------------------ #
    #  Relative mode arguments                                             #
    # ------------------------------------------------------------------ #
    rel_grp = parser.add_argument_group(
        "Relative mode",
        "Arguments for relative mode (used when --epoch_srt and --epoch_end are NOT provided).",
    )
    rel_grp.add_argument(
        "-r",
        "--relative_mode",
        action="store_true",
        help="Explicitly enable relative mode. "
        "Forces --epoch_srt and --epoch_end to be ignored (set to None). (optional)",
    )
    rel_grp.add_argument(
        "-rop",
        "--rolling_period",
        action="store_true",
        help="Use a rolling period for splicing. (optional)",
    )
    rel_grp.add_argument(
        "-ror",
        "--rolling_ref",
        default="-1",
        help="Reference for the rolling period (datetime-like or int). "
        "Use -1 for the last epoch. Defaults to -1. (optional)",
    )
    rel_grp.add_argument(
        "-rnd",
        "--round_method",
        default="floor",
        help="Method for rounding epochs during the splice operation. "
        "Defaults to 'floor'. (optional)",
    )
    rel_grp.add_argument(
        "-der",
        "--drop_epoch_rnd",
        action="store_true",
        help="Drop the rounded epochs during the splice operation. (optional)",
    )

    args = parser.parse_args()

    spc = splice_rnx(
        rnxs_inp=prep_inputs(args.rnxs_inp),
        out_dir=args.out_dir,
        tmp_dir=args.tmp_dir,
        period=args.period,
        log_dir=args.log_dir,
        epoch_srt=args.epoch_srt,
        epoch_end=args.epoch_end,
        relative_mode=args.relative_mode,
        site=args.site,
        data_frequency=args.data_frequency,
        handle_software=args.handle_software,
        rolling_period=args.rolling_period,
        rolling_ref=args.rolling_ref,
        round_method=args.round_method,
        drop_epoch_rnd=args.drop_epoch_rnd,
        rinexmod_options=args.rinexmod_options,
        metadata=args.metadata,
    )

    if spc is not None:
        print(spc)


if __name__ == "__main__":
    main()
