#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 30/05/2024 16:22:55

@author: psakic
"""

import argparse
import os.path

import yaml
import autorino.api as aroapi

def main():
    parser = argparse.ArgumentParser(description="Convert RAW files to RINEX.")
    parser.add_argument("-i",
        "--inp_raws",
        required=True,
        nargs="+",
        help="The input RAW files to be converted "
        "Possible inputs are: \n"
        "* one single RAW file path \n"
        "* a comma-separated (,) list of RAW paths \n"
        "* a text file containing a list of RAW paths \n"
        "(then --list_file_input must be activated) \n"
        "* a directory containing RAW files \n",
    )
    parser.add_argument("-o",
        "--out_dir",
        help="The output directory where the converted files will be stored",
        required=True
    )

    parser.add_argument(
        "-t",
        "--out_structure",
        help="The structure of the output directory. "
             "If provided, the converted files will be "
             "stored in a subdirectory of out_dir following this structure. "
             "See README.md for more information. "
             "Typical values are '<SITE_ID4>/%%Y/' or '%%Y/%%j/ (default).",
        default="%Y/%j",
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
        "-frnx",
        "--force_rnx",
        action="store_true",
        help="Force the conversion even if the output files already exist",
        default=False,
    )

    parser.add_argument(
        "-fraw",
        "--force_raw",
        action="store_true",
        help="Force the RAW file archiving even if the output files already exist",
        default=False,
    )

    parser.add_argument(
        "-l",
        "--list_file_input",
        action="store_true",
        help="If set to True, the input RAW files are provided as a list in a text file",
        default=False,
    )

    parser.add_argument(
        "-tmp",
        "--tmp_dir",
        help="The temporary directory used during the conversion process. "
             "If not provided, it defaults to <$HOME>/autorino_workflow/tmp. ",
        default='<$HOME>/autorino_workflow/tmp',
    )
    parser.add_argument(
        "-log",
        "--log_dir",
        help="The directory where logs will be stored. "
             "If not provided, it defaults to <$HOME>/autorino_workflow/log",
        default='<$HOME>/autorino_workflow/log',
    )
    parser.add_argument(
        "-rimo",
        "--rinexmod_options",
        type=yaml.safe_load,
        help="The options for modifying the RINEX files during the conversion. "
             "The options must be provided in a dictionnary represented as a string "
             "e.g. '{longname: False, filename_style: basic}' "
             "Defaults to None",
        default=None,
    )

    parser.add_argument(
        "-ro",
        "--raw_out_dir",
        help="Directory where RAW files will be archived. "
             "No deletion will occur, your RAW files are sacred.",
        default=None,
    )

    parser.add_argument(
        "-rt",
        "--raw_out_structure",
        help="Structure for archiving RAW files. "
             "Defaults to the same structure as the output directory (-o/--out_dir) if not provided.",
        default=None,
    )

    parser.add_argument(
        "-p",
        "--processes",
        type=int,
        help="Number of processes to use for conversion. "
             "Defaults to 1 (single process).",
        default=1,
    )

    parser.add_argument(
        "-fpt",
        "--filter_prev_tables",
        action="store_true",
        help="If set, filters and skips previously converted files "
             "with tables stored in the tmp tables directory.",
        default=False,
    )

    parser.add_argument(
        "-c",
        "--converter",
        help="The software to be used for converting the RAW files to RINEX. "
             "Default is 'auto' which lets autorino choose the best available converter based on RAW file extension."
             "Possible values are:"
             "* 'auto' (automatic choice based on the extension),"
             "* 'trm2rnx' (Trimble unofficial),"
             "* 't0xconvert' (Trimble official),"
             "* 'runpkr00' (Trimble legacy),"
             "* 'teqc' (legacy conversion & RINEX Handeling),"
             "* 'mdb2rinex' (Leica),"
             "* 'sbf2rin' (Septentrio),"
             "* 'convbin' (BINEX),"
             "* 'tps2rin' (Topcon),"
             "* 'converto' (RINEX Handeling),"
             "* 'gfzrnx' (RINEX Handeling)",
        default="auto",
    )


    args = parser.parse_args()

    aroapi.convert_rnx(
        inp_raws=_prep_raws_inp(args),
        out_dir=args.out_dir,
        out_structure=args.out_structure,
        tmp_dir=args.tmp_dir,
        log_dir=args.log_dir,
        rinexmod_options=args.rinexmod_options,
        metadata=args.metadata,
        force_rnx=args.force_rnx,
        force_raw=args.force_raw,
        raw_out_dir=args.raw_out_dir,
        raw_out_structure=args.raw_out_structure,
        processes=args.processes,
        filter_prev_tables=args.filter_prev_tables,
        converter=args.converter
    )


def _prep_raws_inp(args):
    """
    see also step_fcts.import_files
    """
    if args.list_file_input:
        ### input is a filelist of RINEXs => output is a list
        with open(args.inp_raws[0], "r") as f:
            return f.read().splitlines()
    elif len(args.inp_raws) == 1 and os.path.isdir(args.inp_raws[0]):
        ### input is a directory => output is the directory str
        return args.inp_raws[0]
    else:
        ### input is a single or several RINEXs => output is a list
        # (if one single RINEX file, then it is a singleton list)
        return args.inp_raws

if __name__ == "__main__":
    main()
