<img src="./logo_autorino.png" width="300">

# autorino
_Assisted Unloading, Treatment & Organisation of RINex Observations_

**Version 0.1.0 / 2024-05-29**, README Revision: 2024-05-29

**Authors & Contributors:**
* Pierre Sakic (IPGP-OVS, Paris, France) 
* Patrice Boissier (OVPF-IPGP, La Réunion, France)
* Jean-Marie Saurel (IPGP-OVS, Paris, France)
* Cyprien Griot (OVPF-IPGP, La Réunion, France)
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

### External utilities (GNSS converters)

#### Download
To properly use the _autorino_ package, you need to install the official GNSS raw data converters from the different 
GNSS manufacturers websites.
You can find the official converters here:
##### Leica
converter here: [mdb2rinex](https://myworld-portal.leica-geosystems.com/s/fr/application?c__app=downloads)  
Go in: > Products & Services > Downloads > GRxx receiver > Tools > MDB to RINEX Converter for LINUX.  
see IGSMAIL-8341 for more details.
##### Septentrio
converter here: [sbf2rin](https://www.septentrio.com/en/products/software/rxtools#resources)
##### Topcon
converter here: [tps2rin](https://mytopcon.topconpositioning.com/support/products/tps2rin-converter)  
You need to emulate it with `wine`. Detailled precedure will be added soon.
##### BINEX
converter here: [convbin](https://github.com/rtklibexplorer/RTKLIB)  
`convbin` is part of the RTKLIB package. You can install it from the RTKLIB (explorer version) github repository.  
Detailled procedure will be added soon.
##### Trimble
converter here: [trm2rinex-docker](https://github.com/Matioupi/trm2rinex-docker)    
This docker image is a wrapper around Trimble's official converter `trm2rinex` which is not available for Linux.  
A dedicated README file `trm2rinex_readme.md` details the installation and usage of this docker image.
##### Trimble's runpkr00
for legacy RINEX2 conversion  
converter here: [runpkr00](https://kb.unavco.org/article/trimble-runpkr00-latest-versions-744.html)
##### RINEX handling software
You might also need RINEX handeling/legacy converter software:  
* [teqc](https://www.unavco.org/software/data-management/teqc/teqc.html)  
* [GFZRNX](https://www.gfz-potsdam.de/en/section/global-geodetic-observation-and-modelling/software/gfzrinex/)
* IGN's _converto_  

NB: GFZRNX usage is **not allowed** in _routine mode_ without a proper commercial license. Be sure to comply with it.

#### Setup 
Once the converters are installed, you need to set the converter paths in the _autorino_'s `env` configuration file.

This configuration file is located here:
```autorino/configfiles/env/autorino_env.yml```

To do so, you can:
* set the full executable's paths to the in the `env` configuration file
* set the paths in your `$PATH` environment variable, and then simply set the executable's names in the `env` 
configuration file.


## Getting started: some simple examples

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