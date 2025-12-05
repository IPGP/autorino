#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 05/12/2025 17:37:23

@author: psakic
"""


# Import star style
from pathlib import Path

# from pathlib3x import Path
from geodezyx import utils

# IMPORT AUTORINO ENVIRONNEMENT VARABLES
##software paths
import autorino.cfgenv.env_read as aroenv

# +++ Import the logger
import logging
logger = logging.getLogger("autorino")
logger.setLevel(aroenv.ARO_ENV_DIC["general"]["log_level"])

aro_env_soft_path = aroenv.ARO_ENV_DIC["conv_software_paths"]


def _kw_options_dict2str(kw_options):
    """
    Converts a dictionary of keyword options into a command line string.

    This function takes a dictionary where the keys are command line option flags (e.g., "-a", "-b")
    and the values are the corresponding values for these flags.
    It returns a string that represents these options in a format that can be used in a command line interface.

    Parameters
    ----------
    kw_options : dict
        A dictionary where the keys are command line option flags and the values
        are the corresponding values for these flags.

    Returns
    -------
    cmd_list : list
        A list where the elements are command line options and their values.
    cmd_str : str
        A string that represents the command line options and their values.

    Examples
    --------
    >>> kw_options = {"-a": "valueA", "-b": "42"}
    >>> _kw_options_dict2str(kw_options)
    '-a valueA -b 42'
    """
    cmd_list = []

    if utils.is_iterable(kw_options):
        pass
    else:
        kw_options = [kw_options]

    for kwo in kw_options:
        for key, val in kwo.items():
            cmd_list = cmd_list + [str(key), str(val)]

    cmd_str = " ".join(cmd_list)

    return cmd_list, cmd_str


def _options_list2str(options):
    """
    Converts a list of options into a command line string.

    This function takes a list where the elements are command line options
    (e.g., "-a", Path(valueA), "-b", 42) and returns a string that represents these options
    in a format that can be used in a command line interface.

    Parameters
    ----------
    options : list
        A list where the elements are command line options.

    Returns
    -------
    cmd_list : list of str
        A list where the elements are command line options and their values.
    cmd_str : str
        A string that represents the command line options and their values.

    Examples
    --------
    > options = ["-a", Path(valueA), "-b", 42]
    > _options_list2str(options)
    (['-a', 'valueA', '-b', '42'], '-a valueA -b 42')
    """
    cmd_list = []
    for opt in options:
        if type(opt) is str:
            cmd_list.append(opt)
        else:
            cmd_list = cmd_list + opt

    cmd_str = " ".join(cmd_list)

    return cmd_list, cmd_str


###################################################################
#### command builder functions


# Configuration dictionary for each converter
CONVERTER_CONFIGS = {
    'trm2rinex': {
        'docker_mode': True,
        'base_options': ['-n', '-s', '-v', '3.04', '-p', 'out/'],
        'inp_path_key': 'inp/',
        'out_path_key': '-p',
    },
    't0xconvert': {
        'copy_input': True,
        'base_options': ['-o', '-v304'],
        'append_input': True,
    },
    'mdb2rinex': {
        'base_options': ['--out', None, '--files', None],
        'out_idx': 1,
        'inp_idx': 3,
    },
    'sbf2rin': {
        'base_options': ['-f', None, '-o', None, '-s'],
        'inp_idx': 1,
        'out_idx': 3,
    },
    'runpkr00': {
        'base_options': ['-g', '-d'],
        'append_args': True,
    },
    'convbin': {
        'base_options': ['-d', None, '-os', '-od', '-r', 'binex'],
        'out_idx': 1,
        'append_input': True,
    },
    'tps2rin': {
        'wine_mode': True,
        'base_options': ['-o', None, '-i', None],
        'out_idx': 1,
        'inp_idx': 3,
    },
    'teqc': {
        'base_options': ['+out', None],
        'out_idx': 1,
        'append_args': True,
        'multi_input': True,
    },
    'converto': {
        'base_options': ['-i', None, '-o', None],
        'inp_idx': 1,
        'out_idx': 3,
        'multi_input': True,
    },
    'gfzrnx': {
        'base_options': ['-finp', None, '-fout', None],
        'inp_idx': 1,
        'out_idx': 3,
        'multi_input': True,
    },
}


def cmd_build_generic_converter(
        converter_name,
        inp_raw_fpath,
        out_dir,
        bin_options_custom=[],
        bin_kwoptions_custom=dict(),
        bin_path=None,
):
    """
    Generic command builder for all converters.

    Parameters
    ----------
    converter_name : str
        Name of the converter (e.g., 'sbf2rin', 'teqc')
    inp_raw_fpath : str, Path, or list
        Input file path(s)
    out_dir : str or Path
        Output directory
    bin_options_custom : list, optional
        Custom options
    bin_kwoptions_custom : dict, optional
        Custom keyword options
    bin_path : str, optional
        Binary path (defaults to aro_env_soft_path[converter_name])

    Returns
    -------
    cmd_use, cmd_list, cmd_str : tuple
        Command in various formats
    """

    if bin_path is None:
        bin_path = aro_env_soft_path.get(converter_name, converter_name)

    config = CONVERTER_CONFIGS[converter_name]

    # Convert paths
    out_dir = Path(out_dir)

    # Handle multiple input files
    if config.get('multi_input') and utils.is_iterable(inp_raw_fpath):
        raw_fpath_list = [Path(e) for e in inp_raw_fpath]
        raw_fpath_mono = raw_fpath_list[0]
    else:
        raw_fpath_list = [Path(inp_raw_fpath)]
        raw_fpath_mono = Path(inp_raw_fpath)

    # Build command list
    cmd_list = []

    # Handle special modes
    if config.get('wine_mode'):
        cmd_list.extend(['wine', bin_path])
    elif config.get('docker_mode'):
        cmd_list.extend(_build_docker_prefix(raw_fpath_mono.parent, out_dir))
        cmd_list.append(bin_path)
        if config.get('out_dir_chmod'):
            out_dir.chmod(0o777)
    elif config.get('copy_input'):
        cmd_list.extend(['cp', str(raw_fpath_mono), str(out_dir), '&&'])
        cmd_list.append(bin_path)
        raw_fpath_list = [out_dir / raw_fpath_mono.name]
    else:
        cmd_list.append(bin_path)

    # Build base options with path substitution
    base_opts = config['base_options'].copy()
    out_fpath = _determine_output_path(out_dir, raw_fpath_mono, converter_name)

    if 'out_idx' in config:
        base_opts[config['out_idx']] = str(out_fpath if out_fpath else out_dir)
    if 'inp_idx' in config:
        base_opts[config['inp_idx']] = str(raw_fpath_list[0])

    cmd_list.extend([str(e) for e in base_opts if e is not None])

    # Add custom options
    cmd_opt_list, _ = _options_list2str(bin_options_custom)
    cmd_kwopt_list, _ = _kw_options_dict2str(bin_kwoptions_custom)
    cmd_list.extend(cmd_opt_list)
    cmd_list.extend(cmd_kwopt_list)

    # Append input files if needed
    if config.get('append_input') or config.get('append_args'):
        cmd_list.extend([str(f) for f in raw_fpath_list])

    # Build final outputs
    cmd_list = [str(e) for e in cmd_list]
    cmd_str = " ".join(cmd_list)
    cmd_use = [cmd_str]

    return cmd_use, cmd_list, cmd_str


def _build_docker_prefix(inp_dir, out_dir):
    """Build Docker command prefix."""
    return [
        "docker", "run", "--rm",
        "-v", f"{inp_dir.resolve()}:/inp",
        "-v", f"{out_dir.resolve()}:/out",
    ]


def _determine_output_path(out_dir, raw_fpath, converter):
    """Determine output file path based on converter."""
    if converter in ('sbf2rin', 'teqc', 'converto'):
        return out_dir / f"{raw_fpath.name}.rnx_{converter}"
    return None


# Convenience wrappers (keep for backward compatibility)
def cmd_build_sbf2rin(inp_raw_fpath, out_dir, bin_options_custom=[],
                      bin_kwoptions_custom=dict(), bin_path=None):
    return cmd_build_generic_converter('sbf2rin', inp_raw_fpath, out_dir,
                                       bin_options_custom, bin_kwoptions_custom, bin_path)

# ... repeat for other converters