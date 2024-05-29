<img src="./logo_autorino.png" width="300">

# autorino
_Assisted Unloading, Treatment & Organisation of RINex Observations_

**Version 0.1.0 / 2024-05-29**, README Revision: 2024-05-29

**Authors & Contributors:**
* Pierre Sakic (IPGP-OVS, Paris, France) 
* Patrice Boissier (OVPF-IPGP, La Réunion, France)
* Cyprien Griot (OVPF-IPGP, La Réunion, France)
* Jean-Marie Saurel (IPGP-OVS, Paris, France)

**Contact e-mail:** sakic@ipgp.fr

**Licence:** GNU GPL v3 (see attached license file) 

## Introduction

The `autorino` package (for Assisted Unloading, Treatment & Organisation of RINex Observations) is designed for
automated download and conversion of GNSS raw data from the main manufacturers’ receivers 
(Leica, Septentrio, Topcon, Trimble, and BINEX) based on their respective official conversion utilities. 
A special focus is put on conversion to RINEX3/4 and near real-time capability (download frequency up to 5 min).

`àutorino` aims to perfom the four following tasks:
1. **Download** GNSS raw data from remote GNSS receivers
2. **Conversion** of GNSS raw data to RINEX3/4 format using official conversion utilities from the main GNSS manufacturers.
3. **Handle** RINEX files (e.g., merging, splitting, splicing, etc.) using dedicated utilities.
4. **Metadata edition** of RINEX files (e.g., modifying header metadata, renaming filenames, editing comments, etc.) 
using the spinoff tool `rinexmod`.

## Installation

For the timebeing, the package is not available on PyPi, so you need to install it by adding the path of the `autorino`
package to your Python path.

### External utilities (GNSS converters)

#### Download
To properly use the `autorino` package, you need to install the official GNSS raw data converters from the different 
GNSS manufacturers websites.
You can find the official converters here:
* Leica: [Leica Geo Office](https://leica-geosystems.com/products/gnss-systems/software/leica-geo-office)
* Septentrio: [Septentrio](https://www.septentrio.com/products/software)
* Topcon: [Topcon Tools](https://www.topconpositioning.com/gb/products/software/topcon-tools)
* BINEX: [BINEX](https://www.unavco.org/software/data-management/binex/binex.html)
* Trimble: [Trimble Converters](https://www.trimble.com/Support/Support_A_to_Z.aspx)
* Trimble's runpkr00: [runpkr00](https://www.trimble.com/Support/Support_A_to_Z.aspx) for legacy RINEX2 conversion

You might also need the RINEX handeling software:
* teqc: [teqc](https://www.unavco.org/software/data-management/teqc/teqc.html)
* GFZRNX: [GFZRNX](https://www.gfz-potsdam.de/en/section/global-geodetic-observation-and-modelling/software/gfzrinex/)

#### Setup 
Once the converters are installed, you need to set the converter paths in the `env` configuration file.

This configuration file is located here:
```autorino/configfiles/env/autorino_env.yml```

To do so, you can:
* set the full executable's paths to the in the `env` configuration file
* set the paths in your `$PATH` environment variable, and then simply set the executable's names in the `env` 
configuration file.

## Documentation





