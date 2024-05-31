<img src="./logo_autorino.png" width="300">

# autorino
_Assisted Unloading, Treatment & Organisation of RINex Observations_

**Version 0.1.0 / 2024-05-29**, README Revision: 2024-05-29

**Authors & Contributors:**
* [Pierre Sakic](https://github.com/PierreS-alpha) (IPGP-OVS, Paris, France) 
* [Patrice Boissier](https://github.com/PBoissier) (OVPF-IPGP, La Réunion, France)
* [Jean-Marie Saurel](https://github.com/jmsaurel) (IPGP-OVS, Paris, France)
* [Cyprien Griot](https://github.com/cyprien-griot) (OVPF-IPGP, La Réunion, France)
* Diane Pacaud (OVPF-IPGP, La Réunion, France)
* Aurélie Panetier (IPGP, Paris, France)

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
package to your Python path.

### External dependencies
_autorino_ relies on several external dependencies. Be sure to have them installed on your system using 
```
pip install geodezyx
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
Go in: _Products & Services > Downloads > GRxx receiver > Tools > MDB to RINEX Converter for LINUX._  
see IGSMAIL-8341 for more details.
#### Septentrio
converter here: [sbf2rin](https://www.septentrio.com/en/products/software/rxtools#resources)
#### Topcon
converter here: [tps2rin](https://mytopcon.topconpositioning.com/support/products/tps2rin-converter)  
_autorino_ will emulate it with `wine`. Be sure to have `wine` installed on your computer. Detailled precedure will be added soon.
#### BINEX
converter here: [convbin](https://github.com/rtklibexplorer/RTKLIB)  
`convbin` is part of the RTKLIB package. You can install it from the RTKLIB (explorer version) github repository.  
Detailled procedure will be added soon.
#### Trimble
converter here: [trm2rinex-docker](https://github.com/Matioupi/trm2rinex-docker)    
This docker image is a wrapper around Trimble's official converter `trm2rinex` which is not available for Linux.  
A dedicated README file `trm2rinex_readme.md` details the installation and usage of this docker image.
#### Trimble's runpkr00
for legacy RINEX2 conversion  
converter here: [runpkr00](https://kb.unavco.org/article/trimble-runpkr00-latest-versions-744.html)
#### RINEX handling software
You might also need RINEX handeling/legacy converter software:  
* [teqc](https://www.unavco.org/software/data-management/teqc/teqc.html)  
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

### Call the conversion function
arocmn.convert_rnx(l,out_dir,out_dir)
```

#### convert_rnx function docstring
``` python
def convert_rnx(raws_inp, out_dir, tmp_dir, log_dir=None,
                rinexmod_options=None,
                metadata=None):
    """
    Frontend function to perform RAW > RINEX conversion

    Parameters
    ----------
    raws_inp : list
        The input RAW files to be converted
    out_dir : str
        The output directory where the converted files will be stored
    tmp_dir : str
        The temporary directory used during the conversion process
    log_dir : str, optional
        The directory where logs will be stored. If not provided, it defaults to tmp_dir
    rinexmod_options : dict, optional
        The options for modifying the RINEX files during the conversion
    metadata : dict, optional
        The metadata to be included in the converted RINEX files

    Returns
    -------
    None
    """
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
* `handle` : handle the data (not implemented yet)

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

### aliases in the configuration files

To use generic or variables values in the configuration files, you can use aliases.
Aliases take the form of `<aliasname>` or `<ALIASNAME>` with `< >`. Alias are case-sensitive: 
the first version is lower-case and the latter is upper-case.
The following aliases are managed:
* `<site_id4>` or `<SITE_ID4>`: the 4-characters site name
* `<site_id9>` or `<SITE_ID9>`: the 9-characters site name

Time aliases can also be used. They follow the `date` format convention, 
e.g. `%Y` for the year, `%H` for the hour, `%j` for the day of year, etc... 

Pper default values can be called and used in the configuration files using the alias:
* `FROM_MAIN`. Then, the value is taken from the _main_ configuration file, see above
* `FROM_SESSION`. Then, the value is taken from the `session` block

## Under the hood

_autorino_ is based on a main parent class: `StepGnss`. 
It performs generic actions on input files, saving them in an output folder.

`StepGnss` has three daughter classes: 
* `DownloadGnss`: for downloading a RAW file to the local server 
* `ConvertGnss`: for RAW > RINEX conversion
* `HandleGnss`: to perform decimation, spliting or splicing operations on a RINEX

The central attribute of a `StepGnss` object is its table (`step_gnss.table`). 

This is a pandas' DataFrame that lists, among other things, the input files, and, 
where applicable, the output files if the operation has been successful.