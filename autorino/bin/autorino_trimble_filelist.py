#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 19/09/2024 16:02:51

@author: psakic
"""

import argparse
import autorino.check as arochk

#### Import the logger
import logging
import autorino.cfgenv.env_read as aroenv

logger = logging.getLogger(__name__)
logger.setLevel(aroenv.aro_env_dict["general"]["log_level"])

def main():
    """
    Shell function to call trimble_filelist_html with command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Generate a list of Trimble files from a remote HTML directory.")
    parser.add_argument("site", type=str, help="The site identifier.")
    parser.add_argument("hostname", type=str, help="The hostname of the remote server.")
    parser.add_argument("output_dir", type=str,
                        help="The directory where the downloaded HTML files will be saved.")
    parser.add_argument("start_date",
                        help="The start date for the file search.")
    parser.add_argument("end_date",
                        help="The end date for the file search.")
    parser.add_argument("--period", type=str, default="1M",
                        help="The period for the file search. Default is '1M'.")
    parser.add_argument("--structure", type=str, default="download/Internal/%Y%m",
                        help="The directory structure on the remote server. Default is 'download/Internal/Ym'.")

    args = parser.parse_args()

    arochk.trimble_filelist_html(
        site=args.site,
        host_name=args.host_name,
        output_dir=args.output_dir,
        start_date=args.start_date,
        end_date=args.end_date,
        period=args.period,
        structure=args.structure
    )

if __name__ == "__main__":
    main()