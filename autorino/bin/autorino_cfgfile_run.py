import argparse
import autorino.api as aroapi


def main():
    ##### Parsing Args
    parser = argparse.ArgumentParser(
        description="Assisted Unloading, Treatment and Organization of RINEX observations"
    )

    parser.add_argument(
        "-c",
        "--config",
        type=str,
        help="The input configuration file or directory of configuration files. "
             "If a directory is provided, all files ending with '.yml' will be used.",
        default="",
        required=True
    )
    parser.add_argument(
        "-m",
        "--main_config",
        type=str,
        help="The main configuration file to be used.",
        default="",
    )
    parser.add_argument(
        "-s",
        "--start",
        type=str,
        help="The start date for the epoch range. "
             "Can be a list; if so, each epoch is considered separately. "
             "Can be a file path; if so, the file contains a list of start epochs. "
             "Default is None.",
        default=None,
    )
    parser.add_argument(
        "-e",
        "--end",
        type=str,
        help="The end date for the epoch range. Default is None.",
        default=None,
    )
    parser.add_argument(
        "-inpdir",
        "--period",
        type=str,
        help="The period for the epoch range. Default is '1D'.",
        default="1D",
    )
    parser.add_argument(
        "-ls",
        "--list_sites",
        type=str,
        help="A list of site identifiers to filter the configuration files."
             "If provided, only configurations for sites in this list will be processed. "
             "Default is None.",
        default="",
    )
    parser.add_argument(
        "-ss",
        "--steps_select_list",
        type=str,
        help="A list of selected steps to be executed."
             "If not provided, all steps in 'steps_lis' will be executed. "
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
        default=False,
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="If True, the steps will be executed even if the output files already exist. "
             "Overrides the 'force' parameters in the configuration file. "
             "Default is False.",
        default=False,
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
