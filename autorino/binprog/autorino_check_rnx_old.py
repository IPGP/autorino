#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 18/01/2025 17:30:33

@author: psakic
"""


import argparse
import logging
import pandas as pd
from datetime import datetime
from autorino.check import check_rinex

# Configure logging
logger = logging.getLogger('autorino')
logging.basicConfig(level=logging.INFO)

def main():
    """
    Shell function to call check_rinex with command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Check the existence of RINEX files in an archive."
    )
    parser.add_argument(
        "rinex_dir", type=str, help="Parent directory of a RINEX archive."
    )
    parser.add_argument(
        "start", type=str, help="Start date of the wished period (YYYY-MM-DD)."
    )
    parser.add_argument(
        "end", type=str, help="End date of the wished period (YYYY-MM-DD)."
    )
    parser.add_argument(
        "--silent", action="store_true", help="Do not print the tables in the console."
    )
    parser.add_argument(
        "--return_concat_df", action="store_true", help="Return concatenated DataFrames."
    )

    args = parser.parse_args()

    start_date = datetime.strptime(args.start, "%Y-%m-%d")
    end_date = datetime.strptime(args.end, "%Y-%m-%d")

    df_analyze, df_simple_color, df_issue = check_rinex(
        rinex_dir=args.rinex_dir,
        start=start_date,
        end=end_date,
        silent=args.silent,
        return_concat_df=args.return_concat_df
    )

    if not args.silent:
        print("RINEXs summary:")
        print(df_simple_color.to_string())
        print("RINEXs issues:")
        print(df_issue.to_string())

if __name__ == "__main__":
    main()