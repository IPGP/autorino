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

logger = logging.getLogger("autorino")
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])


def main():
    """
    Shell function to call trimble_filelist_html with command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Generate a list of Trimble files from a remote HTML directory.",
        epilog="Example: autorino_trimble_filelist CBEZ <URL_of_CBEZ> /output/directory 2024-01-01 2024-12-31'",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("site", type=str, help="The site identifier (4 characters).")
    parser.add_argument("hostname", type=str, help="The hostname of the remote server.")
    parser.add_argument(
        "output_dir",
        type=str,
        help="The directory where the downloaded HTML files will be saved.",
    )
    parser.add_argument("start_date", help="The start date for the file search.")
    parser.add_argument("end_date", help="The end date for the file search.")
    parser.add_argument("-p",
        "--period",
        type=str,
        default="1ME",
        help="The period for the file search, usually a month. Default is '1ME'.",
    )
    parser.add_argument("-t",
        "--structure",
        type=str,
        default="download/Internal/%Y%m",
        help=r"The directory structure on the remote server. Default is 'download/Internal/\%Y\%m'.",
    )

    args = parser.parse_args()

    arochk.trimble_filelist_html(
        site=args.site,
        hostname=args.hostname,
        output_dir=args.output_dir,
        start_date=args.start_date,
        end_date=args.end_date,
        period=args.period,
        structure=args.structure,
    )


if __name__ == "__main__":
    main()
