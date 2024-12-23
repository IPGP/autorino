<img src="./logo_autorino.png" width="300">

# autorino
autorino is a tool for _Assisted Unloading, Treatment & Organisation of RINex Observations_  🛰️ 🌐 🦏 

**Version: 0.1.0**
**Date: 2024-05-29**, README Revision: 2024-05-29

**Authors & Contributors:**
* [Pierre Sakic](https://github.com/PierreS-alpha) (IPGP-OVS, Paris, France) 
* [Patrice Boissier](https://github.com/PBoissier) (OVPF-IPGP, La Réunion, France)
* [Jean-Marie Saurel](https://github.com/jmsaurel) (IPGP-OVS, Paris, France)
* [Cyprien Griot](https://github.com/cyprien-griot) (OVPF-IPGP, La Réunion, France)
* [Diane Pacaud](https://github.com/DianouPac) (OVPF-IPGP, La Réunion, France)
* [Aurélie Panetier](https://github.com/aureliep972) (IPGP, Paris, France)

**Contact e-mail:** sakic@ipgp.fr

**Licence:** GNU GPL v3 (see attached license file) 

## Introduction

The _autorino_ package (for _Assisted Unloading, Treatment & Organisation of RINex Observations_) is designed for
automated download and conversion of GNSS raw data from the main manufacturers’ receivers 
(Leica, Septentrio, Topcon, Trimble, and BINEX) based on their respective official conversion utilities. 
A special focus is put on conversion to RINEX3/4 and near real-time capability (download frequency up to 5 min).

_autorino_ aims to perfom the four following tasks:
1. **Download** GNSS raw data from remote GNSS receivers
2. **Conversion** of GNSS raw data to RINEX3/4 format using official conversion utilities from the main GNSS manufacturers.
3. **Handle** RINEX files (e.g., merging, splitting, splicing, etc.) using dedicated utilities.
4. **Metadata edition** of RINEX files (e.g., modifying header metadata, renaming filenames, editing comments, etc.) 
based on _autorino_'s spinoff tool [_rinexmod_](https://github.com/IPGP/rinexmod).

## Installation


For the time being, the package is not available on PyPi, so you need to install it by adding the path of the _autorino_
package to your `$PYTHONPATH` in your _.bashrc_.
```bash
PYTHONPATH=$PYTHONPATH:/home/user/path_to/autorino
```

If you want to use _autorino_ in CLI mode, you must also add the path to the _autorino_ script to your `$PATH` in your _.bashrc_.
```bash
$PATH=$PATH:/home/user/path_to/autorino/autorino
``` 
Note that it is `autorino/autorino` two times, since the CLI programs are inside the _autorino_'s module.

### External dependencies
_autorino_ relies on several external dependencies. Be sure to have them installed on your system using 
```
pip install -r /home/user/path_to/autorino/requirements.txt
```

### Setting up the environment

You need to set up the environment variable `$AUTORINO_ENV` to point to the _autorino_'s configuration file.

In your .bashrc or .bash_profile file, add the following lines:
```bash
export AUTORINO_ENV="/home/user/path_to/autorino/configfiles/env/autorino_env.yml"
```
This configuration file is a YAML file that contains the paths to the different GNSS raw data converters, described in the next section below.

If `$AUTORINO_ENV` is not set, _autorino_ will use the default configuration file located in the package's `configfiles/env/` folder.  
Per defaults values assume that the converter executables are known by your system and (e.g. set in your `$PATH`).

## External utilities (GNSS converters)

### Download external utilities
To properly use the _autorino_ package, you need to install the official GNSS raw data converters from the different 
GNSS manufacturers websites.
You can find the official converters here:
#### Leica
converter here: [mdb2rinex](https://myworld-portal.leica-geosystems.com/s/fr/application?c__app=downloads)  
Go in: _Products & Services > Downloads > GNSS Products > GRxx receiver > Tools > MDB to RINEX Converter for LINUX._  
see IGSMAIL-8341 for more details.
#### Septentrio
converter here: [sbf2rin](https://www.septentrio.com/en/products/software/rxtools#resources)
#### Topcon
converter here: [tps2rin](https://mytopcon.topconpositioning.com/support/products/tps2rin-converter)  
_autorino_ will emulate it with _wine_. Be sure to have `wine` installed on your computer. Detailled precedure will be added soon.
#### BINEX
converter here: [convbin](https://github.com/rtklibexplorer/RTKLIB)  
_convbin_ is part of the RTKLIB package. You can install it from the RTKLIB (explorer version) github repository.  
Detailled procedure will be added soon.
#### Trimble (official Linux converter)
Ask Trimble support for the official Linux converter _t0xConverter_.
#### Trimble (unofficial dockerized converter)
converter here: [trm2rinex-docker](https://github.com/Matioupi/trm2rinex-docker)    
This docker image is a wrapper around Trimble's official converter _trm2rinex_ which is not available for Linux.  
A dedicated README file `trm2rinex_readme.md` details the installation and usage of this docker image.  
It relies on Trimble's official converter for Windows `ConvertToRinex` available 
[here](https://geospatial.trimble.com/en/support) & [there](https://trl.trimble.com/docushare/dsweb/Get/Document-1051259/).

#### Trimble's runpkr00
for legacy RINEX2 conversion with _teqc_ 
converter here: [runpkr00](https://kb.unavco.org/article/trimble-runpkr00-latest-versions-744.html)
#### teqc
for legacy RINEX2 conversion with the well-known but discontinued UNAVCO's _teqc_ software 
converter here: [teqc](https://www.unavco.org/software/data-management/teqc/teqc.html)
#### RINEX handling software
You might also need RINEX handeling software:  
* [teqc](https://www.unavco.org/software/data-management/teqc/teqc.html)  (for legacy RINEX2 only)
* [GFZRNX](https://www.gfz-potsdam.de/en/section/global-geodetic-observation-and-modelling/software/gfzrinex/)
* IGN's _converto_  

NB: GFZRNX usage is **not allowed** in _routine mode_ without a proper commercial license. Be sure to comply with it.

### Setting up external utilities
Once the converters are installed, you need to set the converter paths in the _autorino_'s `env` configuration file.

You must have set the `$AUTORINO_ENV` environment variable to point to the `env` configuration file. 
(see dedicated section above)

To configure the external utilities, in the you can:
* set the full executable's paths to the in the `env` configuration file
* set the paths in your `$PATH` environment variable, and then simply set the executable's names in the `env` 
configuration file.

## Getting started: some simple examples

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

## The configuration files

_autorino_ relies on YAML configuration files to perform its _workflow_ 
(i.e. set of _steps_) operations.

### The _env_ configuration file

Described in the _Setting up the environment_ and _Setting up external utilities_ 
sections above.

### The _sites_ configuration files

It contains the site-specific information and configuration under the main `station` block. 
Then, it is organized in different sub-blocks:
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
    * `epoch_range` : the epoch range of the step i.e. a start epoch (`epoch1`), an end epoch (`epoch2`), and `period` (step) 
       of the session to download the data. `epoch1` and `epoch2` can be relative epochs in human readable sentences.
      (interpretation done with the [dateparser](https://github.com/scrapinghub/dateparser/) package).
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

### The _main_ configuration file

It contains the "standard" configuration for an _autorino_ workflow,
i.e. all the parameters, paths, options ... which are the same for all stations.
_main_ values can be called and used in the _sites_ configuration files using the alias `FROM_MAIN`
(see below).

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

Per default values can be called and used in the configuration files using the alias:
* `FROM_MAIN`. Then, the value is taken from the _main_ configuration file, see above
* `FROM_SESSION`. Then, the value is taken from the `session` block

## Under the hood

_autorino_ is based on a main parent class: `StepGnss`. 
It performs generic actions on input files, saving them in an output folder.

`StepGnss` has three daughter classes: 
* `DownloadGnss`: for downloading a RAW file to the local server 
* `ConvertGnss`: for RAW > RINEX conversion
* `HandleGnss`: to perform decimation, spliting or splicing operations on a RINEX. It has two daughter classes:
  * `SplitGnss`: to split a RINEX file
  * `SpliceGnss`: to splice (concatenate) RINEX files

The central attribute of a `StepGnss` object is its table (`step_gnss.table`). 

This is a pandas' DataFrame that lists, among other things, the input files, and, 
where applicable, the output files if the operation has been successful.

