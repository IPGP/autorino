```{eval-rst}
.. _config_files_nutshell:
```

## Configuration files in a nutshell

_autorino_ relies on YAML configuration files to perform its _workflow_
(i.e. set of _steps_) operations.

### Location of the configuration files

The exemple configuration files are located in the `configfiles` directory of the _autorino_ package.
They are organized in subdirectories according to their purpose.
But you can also create your own configuration files in a different location with a different folder structure.

The exemple folder structure is as follows:
* `configfiles/main/` for _main_ configuration: general settings regarding autorino's environnement (converters paths
  etc.) and GNSS network
  (GNSS network name, GNSS network's site log path, etc.)
* `configfiles/site/` for _site_-specific configuration: IP addresses, site names, login & password, etc.)
* `configfiles/profile/` for _profile_ configuration: profiles are common settings for a group of sites (same
  manufacturer, same
  data structure, same data transfer protocol, etc.). A site can be part of several profiles.

autorino keeps a philosophy of _one site configuration file per GNSS station_.

### The include section

The `include` section allows you to include other configuration files in the current configuration file,
typically a site configuration file.
This is useful for modularizing your configuration and reusing common settings across different files.  
The `include` section is a list of the configuration files paths you want to include.  
The included files are processed in the order they are listed, and their contents are merged into the current
configuration file, but __prior__ to its content.  
In other words, the values of the first included file is loaded before the next one, and then the next one
complete/overrides the
values of the previous. The current configuration file is processed after all the included files have been processed.  
This means that if there are any overlapping keys or sections, the values of the last file processed will take
precedence.
The included files can be either absolute or relative paths.

#### Example of the include section

In the site configuration file `autorino_site_trimble_cfg.yml`, we include with the `include` section:

```yaml
include:
  - ../main/autorino_main_cfg.yml
  - ../profile/autorino_profile_session24h30s_trimble_cfg.yml
```

The above example includes in the current configuration file:

* `autorino_main_cfg.yml` for the general configuration regarding autorino's environnement and GNSS network
* `autorino_profile_session24h30s_trimble_cfg.yml` configuration file is a common profile for all Trimble stations (with
  the same `inp_file_regex`, `inp_dir_structure`...)

You can control the good inclusion of the configuration files with the `autorino_cfgfile_check`_ command.
See the [cookbook](cookbook.md) for more details.

### The configuration file's main sections

It contains the site-specific information and configuration under the main `station` block.
Then, it is organized in different sub-blocks.

Next chapter [configuration file details](config_file_details.md) all the options.

* `environment`: global settings for the GNSS data processing environment, including paths to software tools and general
  application settings.
    * `conv_software_paths`: paths to GNSS raw data converters
    * `general`: general settings for the configuration file
* `include`: list of the configuration files to include in the current configuration file, see next section.
* `site`: site's name, its coordinates, and metadata
* `device`: manually define the device's (receiver and antenna) characteristics if metadata are not provided in
  `site` block
* `access` : connexion protocols, login and password etc...
* `sessions` : define the record sessions characteristics.
  Each session is in a sub-block with its own parameters.
    * `session_<sessionname>` : define one record session characteristics.
      The session block name is, by convention, `session_<sessionname>`, where `<sessionname>` is also the first
      session's `general` sub-block attribute's `name`.
        * `general` : name, data freqency, temporary and log directories of the session
        * `epoch_range` : See the dedicated section below.
        * `steps` : list of the steps constituting the workflow.
          Each step is a sub-block with its own parameters.

The different possible steps are:

* `download` : download the data
* `convert` : convert the data
* `splice` : splice (concatenate) the data
* `split` : split the data

A step has the following generic structure:

* `active`: a boolean (`True` or `False`) to activate or deactivate the step
* `inp_dir_parent`: the parent directory of the input files
* `inp_structure`: the filename structure of the input files
* `out_dir_parent`: the parent directory of the output files
* `out_structure`: the filename structure of the output files
* `epoch_range`: the epoch range of the step. (see above)
* `options`: a dictionary of options specific to the step

### Aliases in the configuration files

To use generic or variables values in the configuration files, you can use aliases.
Aliases take the form of `<aliasname>` or `<ALIASNAME>` with `< >`. Alias are case-sensitive:
the first version is lower-case and the latter is upper-case.
The following aliases are managed:

* `<site_id4>` or `<SITE_ID4>`: the 4-characters site name
* `<site_id9>` or `<SITE_ID9>`: the 9-characters site name

Time aliases can also be used. They follow the `date` format convention,
e.g. `%Y` for the year, `%H` for the hour, `%j` for the day of year, etc...

The environment variables can also be used as aliases. They follow the `<$ENVVAR>` convention,
using `$` and between `<` & `>`, e.g. `<$HOME>` for the home directory.

### Reserved keywords

Per default values can be called and used in the configuration files using reserved keywords:

* `FROM_SESSION`: Then, the value is taken from the `session` block
* `FROM_MAIN`: Now obsolete and deprecated since introduction of `include` in version 2.0.0.


