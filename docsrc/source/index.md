```{eval-rst}
.. autorino documentation master file, created by
   sphinx-quickstart on Wed Apr  9 11:49:52 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.
```

# Welcome to _autorino_'s documentation!
```{eval-rst}
.. figure::  logo_autorino.png
   :width: 250px
   :align: center
```

autorino is a tool for _Assisted Unloading, Treatment & Organisation of RINex Observations_  🛰️ 🌐 🦏 

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

## References
If you find _autorino_ useful for your research, please consider citing the following reference:
* Sakic, P., Boissier, P., Saurel, J.-M., Deroussi, S., Andrieu, A., Griot, C., Bosson, A., Vidal, C., Pardo, C., de Chabalier, J.-B., and OVPF, OVSG & OVSM Teams: _Modernizing GNSS data acquisition, pre-processing, and distribution at volcanological observatories_,
 Geosci. Instrum. Method. Data Syst., 15, 89–106, https://doi.org/10.5194/gi-15-89-2026, 2026.
* Sakic, P., Boissier, P., Saurel, J.-M., Griot, C., Pacaud, D., Boulvais-Abbas, L. (2026).
rinexmod & autorino: Two Tools to Enable Multi-GNSS and Near Real-Time Data Acquisition and Pre-processing. In: International Association of Geodesy Symposia. Springer, Berlin, Heidelberg. https://doi.org/10.1007/1345_2026_327

## Authors and contributors

* [Pierre Sakic](https://github.com/PierreS-alpha) (IPGP-OVS, Paris, France) 
* [Patrice Boissier](https://github.com/PBoissier) (OVPF-IPGP, La Réunion, France)
* [Jean-Marie Saurel](https://github.com/jmsaurel) (IPGP-OVS, Paris, France)
* [Diane Pacaud](https://github.com/DianouPac) (OVPF-IPGP, La Réunion, France)

**Contact e-mail:** sakic@ipgp.fr

**Licence:** GNU GPL v3 (see attached license file) 


```{eval-rst}
------------------
Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

--------
Contents
--------
.. toctree::
   :maxdepth: 3

   self
   installation
   external_converters
   cookbook
   config_files_nutshell
   config_files_details
   under_hood
   autorino
```


