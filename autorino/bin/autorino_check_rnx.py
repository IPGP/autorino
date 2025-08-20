#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 27/01/2025 20:18:31

@author: psakic
"""

import argparse
import pandas as pd
from autorino.api.check_rnx import check_rnx


def main():
    # Get the docstring from check_rnx function for the description
    description = "Checks the presence of RINEX files in the input directory over a specified time range, and computes their completeness ratio."

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-i",
        "--input_dir_parent",
        required=True,
        help="Path to the parent input directory containing RINEX files.",
    )
    parser.add_argument(
        "-t",
        "--input_dir_structure",
        required=False,
        help="Input directory structure pattern for organizing RINEX files. (optional)",
        default="",
    )
    parser.add_argument(
        "-s",
        "--epoch_start",
        required=True,
        help="Start epoch for the time range to check."
    )
    parser.add_argument(
        "-e",
        "--epoch_end",
        required=True,
        help="End epoch for the time range to check."
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Path to the output directory for generated files (csv, plots, etc.). (optional)"
    )
    parser.add_argument(
        "-l",
        "--sites_list",
        nargs="+",
        help="List of specific sites to check. If not provided, all sites will be processed. (optional)",
        default=[],
    )

    args = parser.parse_args()

    # Call the check_rnx function
    _ = check_rnx(
        inp_dir_parent=args.input_dir_parent,
        inp_dir_structure=args.input_dir_structure,
        epoch_start=args.epoch_start,
        epoch_end=args.epoch_end,
        sites_list=args.sites_list,
        output_dir=args.output,
    )

if __name__ == "__main__":
    main()
