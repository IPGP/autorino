#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 29/04/2025 12:18:06

@author: psakic
"""

import autorino.cfgfiles as arocfg
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Check autorino configuration file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-c",
        "--config",
        type=str,
        help="The input site configuration file or directory of sites configuration files. "
        "If a directory is provided, all files ending with '.yml' will be used.",
        required=True,
    )
    parser.add_argument(
        "-i",
        "--include_config",
        type=str,
        nargs="+",
        help="The main configuration file to be used.",
        default=None,
    )

    args = parser.parse_args()

    arocfg.read_cfg(site_cfg_path=args.config,
                    include_cfg_paths_xtra=args.include_config,
                    verbose_debug=True)

if __name__ == "__main__":
    main()
