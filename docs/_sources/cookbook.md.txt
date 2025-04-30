```{eval-rst}
.. _cookbook:
```

## _autorino_'s cookbook 

### Receipe #1: run an _autorino_ workflow

Call `autorino_cfgfile_run` to run an _autorino_ workflow.

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

### Check a configuration file
Call `autorino_cfgfile_check` to check the import of a configuration file, especially its _include_.


#### Synopsis

```{eval-rst}
.. command-output:: autorino_cfgfile_check --help
   :shell:
```