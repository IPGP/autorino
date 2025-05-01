```{eval-rst}
.. _cookbook:
```

## _autorino_'s exemple cookbook

### Receipe #1: run an _autorino_ workflow

Call `autorino_cfgfile_run` to run an _autorino_ workflow i.e. a set of _steps_.  
The workflow is defined in a YAML _site_ configuration file.  
See the next chapters [configuration files in a nutshell](config_files_nutshell.md) &
[configuration files details](config_files_details.md) for more details.

#### Synopsis

```{eval-rst}
.. command-output:: autorino_cfgfile_run --help
   :shell:
```

#### Examples

We set the configuration file path in an environment variable `$ARO_CFGFILE`.

```bash
ARO_CFGFILE=${AUTORINO_DIR}/configfiles/site/autorino_site_cfg.yml
```

##### Launching for specific dates

Run all config files in the sites/terrestrial folder for a 10-day period in the past starting from January 1, 2025

```bash
autorino_cfgfile_run -s '2025-01-01' -e '10 day ago' -c ${ARO_CFGFILE}
```

##### Launching specific steps

Use `-ss/--select_steps`. For example, to run only the download and conversion steps:

```bash
autorino_cfgfile_run -ss download convert -c ${ARO_CFGFILE}
```

##### Excluding specific steps

Use `-ss/--select_steps` to select the steps to exclude, then activate `-es/--exclude_steps_select`.

```bash
autorino_cfgfile_run -ss download -es -m ${ARO_CFG_MAIN_FILE} -c ${ARO_CFGFILE}
```

##### Launching for specific sites

Use `-ls/--list_sites` to run a specific site. For example, to run the site `SOUF00GLP` & `BULG00GLP`:

```bash
autorino_cfgfile_run -ls SOUF00GLP BULG00GLP -m ${ARO_CFG_MAIN_FILE} -c ${ARO_CFGFILE}
```

### Receipe #2: convert RAW to RINEX files

Call `autorino_convert_rnx`_ to convert RAW files to RINEX files.

#### Synopsis

```{eval-rst}
.. command-output:: autorino_convert_rnx --help
   :shell:
```

### Receipe #3: Check a configuration file

Call `autorino_cfgfile_check` to check the import of a configuration file, especially its _include_.

#### Synopsis

```{eval-rst}
.. command-output:: autorino_cfgfile_check --help
   :shell:
```

### Receipe #4: Convert RAW file to RINEX in API mode

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

#### convert_rnx function docstring

```{eval-rst}
.. autofunction:: autorino.api.convert_rnx
```

#### `convert_rnx` function definition

[go to source code](https://github.com/IPGP/autorino/blob/main/autorino/common/frontend_fcts.py#:~:text=convert_rnx)
