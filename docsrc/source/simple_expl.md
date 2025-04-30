```{eval-rst}
.. _simple_expl:
```

## Getting started: some simple examples

### Convert RAW file to RINEX in CLI mode

#### `autorino_convert_rnx` minimal example
``` bash
python3 autorino_convert_rnx.py  --force  --metadata /home/user/path/of/your/sitelogs  --out_dir_structure '<SITE_ID4>/%Y' --list_file_input  /home/user/where_your/raw_data/are_stored/raw_data_list.txt /home/user/where_your/rinex_data/will_be_saved/```
```

#### `autorino_convert_rnx` help
``` 
usage: autorino_convert_rnx.py [-h] [-l] [-s OUT_DIR_STRUCTURE] [-tmp TMP_DIR]
                               [-log LOG_DIR] [-rnmo RINEXMOD_OPTIONS]
                               [-m METADATA] [-f]
                               raws_inp [raws_inp ...] out_dir

Convert RAW files to RINEX.

positional arguments:
  raws_inp              The input RAW files to be convertedPossible inputs
                        are: * one single RAW file path * a list of RAW path *
                        a text file containing a list of RAW paths (then
                        --list_file_input must be activated) * a directory
                        containing RAW files
  out_dir               The output directory where the converted files will be
                        stored

options:
  -h, --help            show this help message and exit
  -l, --list_file_input
                        If set to True, the input RAW files are provided as a
                        list in a text file
  -s OUT_DIR_STRUCTURE, --out_dir_structure OUT_DIR_STRUCTURE
                        The structure of the output directory.If provided, the
                        converted files will be stored in a subdirectory of
                        out_dir following this structure.See README.md for
                        more information.Typical values are '<SITE_ID4>/%Y/'
                        or '%Y/%j/
  -tmp TMP_DIR, --tmp_dir TMP_DIR
                        The temporary directory used during the conversion
                        process
  -log LOG_DIR, --log_dir LOG_DIR
                        The directory where logs will be stored. If not
                        provided, it defaults to tmp_dir
  -rnmo RINEXMOD_OPTIONS, --rinexmod_options RINEXMOD_OPTIONS
                        The options for modifying the RINEX files during the
                        conversion
  -m METADATA, --metadata METADATA
                        The metadata to be included in the converted RINEX
                        files. Possible inputs are: * list of string (sitelog
                        file paths), * single string (single sitelog file
                        path), * single string (directory containing the
                        sitelogs), * list of MetaData objects, * single
                        MetaData object
  -f, --force           Force the conversion even if the output files already
                        exist
```

### Call a Step workflow in CLI mode

#### `autorino_cfgfile_run` minimal example
``` bash
python3 autorino_cfgfile_run.py  -c /path/to/your/configfile.yml -m /path/to/your/main_configfile.yml -s '2024-05-01 00:00:00' -e '2024-05-05 23:59:59' -p '01D' -ls 'SITE' -ss 'download,convert,splice' -f```
```

#### `autorino_cfgfile_run` help
```
usage: autorino_cfgfile_run.py [-h] [-c CONFIG] [-m MAIN_CONFIG] [-s START]
                               [-e END] [-p PERIOD] [-ls LIST_SITES]
                               [-ss STEPS_SELECT_LIST] [-es] [-f]

Assisted Unloading, Treatment and Organization of RINEX observations

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        cfgfiles file path or directory path containing the
                        cfgfiles file
  -m MAIN_CONFIG, --main_config MAIN_CONFIG
                        main cfgfiles file path
  -s START, --start START
  -e END, --end END
  -p PERIOD, --period PERIOD
  -ls LIST_SITES, --list_sites LIST_SITES
                        Comma-separated list of site identifiers
  -ss STEPS_SELECT_LIST, --steps_select_list STEPS_SELECT_LIST
                        Comma-separated list of selected steps to be executed.
                        The step's names are the ones in the config file
                        (download, convert...)
  -es, --exclude_steps_select
                        Flag to exclude the selected steps. The step's names
                        are the ones in the config file (download, convert...)
  -f, --force           force the execution of the steps
```

### Convert RAW file to RINEX in API mode

The most basic and common operation that autorino can perform is to convert some
RAW files to RINEX.

#### convert_rnx function minimal example
``` python
import autorino.common as arocmn
import glob

### Find all BINEX files in a folder
p = "/home/user/where_your/raw_data/are_stored/"
l = glob.glob(p,"*BNX")

### Define the output folder
out_dir = "/home/user/where_your/rinex_data/will_be_saved/"
tmp_dir = out_dir

### Call the conversion function
arocmn.convert_rnx(l,out_dir,tmp_dir)
```

#### `convert_rnx` function definition
[go to source code](https://github.com/IPGP/autorino/blob/main/autorino/common/frontend_fcts.py#:~:text=convert_rnx)