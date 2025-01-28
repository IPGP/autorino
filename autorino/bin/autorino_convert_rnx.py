#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 30/05/2024 16:22:55

@author: psakic
"""

import argparse
import yaml
import autorino.api as aroapi

def main():
    parser = argparse.ArgumentParser(description="Convert RAW files to RINEX.")
    parser.add_argument(
        "raws_inp",
        nargs="+",
        help="The input RAW files to be converted "
        "Possible inputs are: \n"
        "* one single RAW file path \n"
        "* a comma-separated (,) list of RAW paths \n"
        "* a text file containing a list of RAW paths \n"
        "(then --list_file_input must be activated) \n"
        "* a directory containing RAW files \n",
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
        "-t",
        "--out_structure",
        help="The structure of the output directory. "
             "If provided, the converted files will be "
             "stored in a subdirectory of out_dir following this structure. "
             "See README.md for more information. "
             "Typical values are '<SITE_ID4>/%%Y/' or '%%Y/%%j/.",
        default="<SITE_ID4>/%Y/",
    )
    parser.add_argument(
        "-tmp",
        "--tmp_dir",
        help="The temporary directory used during the conversion process. "
             "If not provided, it defaults to <out_dir>/tmp_convert_rnx. ",
        default=None,
    )
    parser.add_argument(
        "-log",
        "--log_dir",
        help="The directory where logs will be stored. "
             "If not provided, it defaults to tmp_dir ",
        default=None,
    )
    parser.add_argument(
        "-rimo",
        "--rinexmod_options",
        type=yaml.safe_load,
        help="The options for modifying the RINEX files during the conversion. "
             "The options must be provided in a dictionnary represented as a string "
             "e.g. '{longname: False, filename_style: basic}' "
             "Defaults to None",
    )
    parser.add_argument(
        "-m",
        "--metadata",
        help="""
        The metadata to be included in the converted RINEX files. \n 
        Possible inputs are: \n 
        * list of string (sitelog file paths)  
        * single string (single sitelog file path) 
        * single string (directory containing the sitelogs)
        """,
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force the conversion even if the output files already exist",
        default=False,
    )

    args = parser.parse_args()

    if args.list_file_input:
        with open(args.raws_inp[0], "r") as f:
            raws_inp = f.read().splitlines()
    else:
        raws_inp = args.raws_inp

    aroapi.convert_rnx(
        raws_inp=raws_inp,
        out_dir=args.out_dir,
        out_structure=args.out_structure,
        tmp_dir=args.tmp_dir,
        log_dir=args.log_dir,
        rinexmod_options=args.rinexmod_options,
        metadata=args.metadata,
        force=args.force,
    )

if __name__ == "__main__":
    main()
