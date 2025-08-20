import argparse
import autorino.api as aroapi
import sys


def main():
    ##### Parsing Args
    parser = argparse.ArgumentParser(
        description="Assisted Unloading, Treatment and Organization of RINEX observations",
        epilog=(
            "Examples:\n"
            "  * run all the config files within cfgfiles_dir directory, using per default epoch ranges:\n"
            "    autorino_cfgfile_run -c cfgfiles_dir\n"
            "  * run the config file site_cfg.yml from the 1st January 2025 for a range of 10 days:\n"
            "    autorino_cfgfile_run -c site_cfg.yml -s 2025-01-01 -e '10 days ago'\n"
            "  * run download and convert steps only for HOUZ00GLP & BORG00REU sites only:\n"
            "    autorino_cfgfile_run -c cfgfiles_dir -si HOUZ00GLP BORG00REU -sp download convert"
        ),
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
        default=None,
        help="The include configuration files to be used for development or advanced purposes. "
        "If a list is provided, all files in the list will be included. "
        "These files override the `include` section of the main configuration file.",
    )
    parser.add_argument(
        "-s",
        "--start",
        type=str,
        help="The start date for the epoch range. "
        "* a litteral, e.g. 'yesterday', '10 days ago' "
        "* YYYY-DDD, year-day of year, e.g. 2025-140 "
        "* YYYY-MM-DD, classic calendar date, e.g. 2025-05-20 "
        "Can also be a list; if so, each epoch is considered separately. "
        "Can also be a file path; if so, the file contains a list of start epochs. "
        "Default is None.",
        default=None,
    )
    parser.add_argument(
        "-e",
        "--end",
        type=str,
        help="The end date for the epoch range. "
        "The epoch can be formatted as: "
        "* a litteral, e.g. 'yesterday', '10 days ago' "
        "* YYYY-DDD, year-day of year, e.g. 2025-140 "
        "* YYYY-MM-DD, classic calendar date, e.g. 2025-05-20 "
        "Default is None.",
        default=None,
    )
    parser.add_argument(
        "-p",
        "--period",
        type=str,
        help="The period for the epoch range i.e. the sampling of the files: "
        "daily = '1D', hourly = '1H', 15 minutes = '15M'. "
        "Default is '1D'.",
        default="1D",
    )
    parser.add_argument(
        "-si",
        "--sites_list",
        type=str,
        nargs="+",
        help="list of site identifiers ('site_id') in the config file "
        "to filter the configuration files. "
        "If provided, only configurations for sites in this list will be processed. "
        "Default is None.",
        default=None,
    )
    parser.add_argument(
        "-xsi",
        "--exclude_sites",
        action="store_true",
        help="If True, the sites in --sites_list will be ignored. "
        "This is the opposed behavior of the regular one using sites_list."
        "Default is False.",
    )
    parser.add_argument(
        "-sp",
        "--steps_list",
        type=str,
        nargs="+",
        help="A list of selected steps to be executed. "
        "If not provided, all steps in the configuration file will be executed. "
        "Default is None.",
        choices=["download", "convert", "split", "splice", "rinexmod"],
        default=None,
    )
    parser.add_argument(
        "-xsp",
        "--exclude_steps",
        action="store_true",
        help="If True the selected steps indicated in step_select_list are excluded. "
        "This is the opposite behavior of the regular one using steps_list. "
        "Default is False.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="If True, the steps will be executed even if the output files already exist. "
        "Overrides the 'force' parameters in the configuration file. "
        "Default is False.",
    )

    args = parser.parse_args()

    config = args.config
    include_config = args.include_config
    start = args.start
    end = args.end
    period = args.period
    sites_list = args.sites_list
    exclude_sites = args.exclude_sites
    steps_list = args.steps_list
    exclude_steps = args.exclude_steps
    force = args.force

    exit_code = aroapi.cfgfile_run(
        cfg_in=config,
        incl_cfg_in=include_config,
        sites_list=sites_list,
        exclude_sites=exclude_sites,
        epo_srt=start,
        epo_end=end,
        period=period,
        steps_list=steps_list,
        exclude_steps=exclude_steps,
        force=force,
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
