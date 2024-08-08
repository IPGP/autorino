#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 30/05/2024 16:22:55

@author: psakic
"""

import argparse
import json
import autorino.common as arocmn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert RAW files to RINEX.")
    parser.add_argument(
        "raws_inp",
        nargs="+",
        help="The input RAW files to be converted"
        "Possible inputs are: \n"
        " * one single RAW file path \n"
        " * a list of RAW path \n"
        " * a text file containing a list of RAW paths \n"
        " (then --list_file_input must be activated) \n"
        " * a directory containing RAW files \n",
    )
    parser.add_argument(
        "out_dir", help="The output directory where the converted files will be stored"
    )
    parser.add_argument(
        "-l",
        "--list_file_input",
        action="store_true",
        help="If set to True, the input RAW files are provided as a list in a text file",
        default=False,
    )
    parser.add_argument(
        "-s",
        "--out_structure",
        help="The structure of the output directory."
             "If provided, the converted files will be stored in a subdirectory of out_dir following this structure."
             "See README.md for more information."
             "Typical values are '<SITE_ID4>/%%Y/' or '%%Y/%%j/",
        default="<SITE_ID4>/%Y/",
    )
    parser.add_argument(
        "-tmp",
        "--tmp_dir",
        help="The temporary directory used during the conversion process",
    )
    parser.add_argument(
        "-log",
        "--log_dir",
        help="The directory where logs will be stored. If not provided, it defaults to tmp_dir",
    )
    parser.add_argument(
        "-rimo",
        "--rinexmod_options",
        type=json.loads,
        help="The options for modifying the RINEX files during the conversion."
             "The options must be provided in a dictionnary represented as a string"
             #"\"'{"name": "img.png","voids": "#00ff00ff","0": "#ff00ff00","100%": "#f80654ff"}'"
             "Defaults to None",
    )
    parser.add_argument(
        "-m",
        "--metadata",
        help="""The metadata to be included in the converted RINEX files. \n Possible inputs are: \n 
                             * list of string (sitelog file paths), 
                             * single string (single sitelog file path),
                             * single string (directory containing the sitelogs),
                             * list of MetaData objects,
                             * single MetaData object""",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force the conversion even if the output files already exist",
        default=False,
    )

    args = parser.parse_args()

    arocmn.convert_rnx(
        args.raws_inp,
        args.out_dir,
        args.tmp_dir,
        args.log_dir,
        args.out_dir_structure,
        args.rinexmod_options,
        args.metadata,
        args.force,
        args.list_file_input,
    )
