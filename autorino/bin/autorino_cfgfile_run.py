import argparse
import autorino.api as aroapi

def main():
    ##### Parsing Args
    parser = argparse.ArgumentParser(
        description="Assisted Unloading, Treatment and Organization of RINEX observations",
        epilog=("Examples:\n"
                "  * run all the config files in the directory cfgfiles_dir, using per default epoch ranges and a main config file:\n"
                "    autorino_cfgfile_run -c cfgfiles_dir -m main_cfg.yml\n"
                "  * run the config file site_cfg.yml from the 2025-10-01 for a range of 10 days:\n"
                "    autorino_cfgfile_run -c site_cfg.yml -s 2025-01-01 -e '10 days ago'\n"
                "  * run download and convert only for HOUZ00GLP & BORG00REU sites only:\n"
                "    autorino_cfgfile_run -c cfgfiles_dir -m main_cfg.yml -ls HOUZ00GLP,BORG00REU -ss download,convert")
    )

    parser.add_argument(
        "-c",
        "--config",
        type=str,
        help="The input site configuration file or directory of sites configuration files. "
             "If a directory is provided, all files ending with '.yml' will be used.",
        required=True
    )
    parser.add_argument(
        "-m",
        "--main_config",
        type=str,
        help="The main configuration file to be used.",
        default=""
    )
    parser.add_argument(
        "-s",
        "--start",
        type=str,
        help="The start date for the epoch range. "
             "Can be a date e.g. '2025-01-01', or a literal e.g. '2 days ago'. "
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
             "Can be a date e.g. '2025-01-01', or a literal e.g. '2 days ago'. "
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
        "-ls",
        "--list_sites",
        type=str,
        help="A list of site identifiers to filter the configuration files. "
             "If provided, only configurations for sites in this list will be processed. "
             "Default is None.",
        default="",
    )
    parser.add_argument(
        "-ss",
        "--steps_select_list",
        type=str,
        help="A list of selected steps to be executed. "
             "If not provided, all steps in 'steps_list' will be executed. "
             "Accepted steps are: 'download', 'convert', 'splice', 'split'. "
             "Default is None.",
        default="",
    )
    parser.add_argument(
        "-es",
        "--exclude_steps_select",
        action="store_true",
        help="If True the selected steps indicated in step_select_list are excluded. "
             "It is the opposite behavior of the regular one using steps_select_list. "
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
    main_config = args.main_config
    start = args.start
    end = args.end
    period = args.period
    list_sites = args.list_sites.split(",") if args.list_sites else None
    steps_select_list = (
        args.steps_select_list.split(",") if args.steps_select_list else None
    )
    exclude_steps_select = args.exclude_steps_select
    force = args.force

    aroapi.cfgfile_run(
        cfg_in=config,
        main_cfg_in=main_config,
        sites_list=list_sites,
        epo_srt=start,
        epo_end=end,
        period=period,
        steps_select_list=steps_select_list,
        exclude_steps_select=exclude_steps_select,
        force=force,
    )

if __name__ == "__main__":
    main()