```{eval-rst}
.. _cookbook:
```

## _autorino_'s exemple cookbook

### Metadata disclaimer
autorino assumes that __the metadata in your RINEX's header are always wrong__.  
Thus, it will always __update the metadata based on an external source__, such as sitelogs or receiver/antenna details given in the site configuration file.

_NB:_ after the conversion step, for receiver's serial number and firmware version, a comparison is made between the exteral metadata source and the newly converted RINEX's header.   
If a difference is detected, a warning is raised, because the RINEX values must be the correct ones.  
Nevertheless, the RINEX header will be updated with the external metadata (the warning is simply an encouragement to change you external metadata source).

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
autorino_cfgfile_run -ss download -es -c ${ARO_CFGFILE}
```

##### Launching for specific sites
Use `-l/--list_sites` to run a specific site. For example, to run the site `SOUF00GLP` & `BULG00GLP`:
```bash
autorino_cfgfile_run -l SOUF00GLP BULG00GLP -c ${ARO_CFGFILE}
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