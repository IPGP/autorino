<img src="./logo_autorino.png" width="300">

# autorino
Assisted Unloading, Treatment & Organisation of RINex Observations

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





