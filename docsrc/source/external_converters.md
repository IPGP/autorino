```{eval-rst}
.. _external_converters:
```

## External GNSS converters

### Setting up external utilities

Be sur to have set `$AUTORINO_ENV` environment variable to point to the configuration file containing the `environment`
section, typically the _main_ configuration file (`autorino_main_cfg.yml`).

Once each manufacturer's converter is downloaded and installed (see below), you need to set the path to each
you need to set the converter paths in the `environment` section of the _main_ configuration file.

To configure the external utilities, you can:  
1. set the full executable's paths in the `environment` section.
2. set the paths in your `$PATH` environment variable, and then simply set the executable's names in the `env`
   configuration file.

The authors recommend the second option, as it is more flexible and easier to maintain.

### Download external GNSS converters

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
_autorino_ will emulate it with _wine_. Be sure to have `wine` installed on your computer. Detailled precedure will be
added soon.

#### BINEX

converter here: [convbin](https://github.com/rtklibexplorer/RTKLIB)  
_convbin_ is part of the RTKLIB package. You can install it from the RTKLIB (explorer version) github repository.

##### detailed procedure

```bash
git clone https://github.com/rtklibexplorer/RTKLIB.git
cd RTKLIB/app/consapp/convbin/gcc
make
```

The compiled binary `convbin` will be in the `RTKLIB/app/consapp/convbin/gcc` folder.

#### Trimble (official Linux converter)

Ask Trimble support for the official Linux converter _t0xConverter_.

#### Trimble (unofficial dockerized converter)

converter here: [trm2rinex-docker-ovs](https://github.com/IPGP/trm2rinex-docker-ovs)    
This docker image is a wrapper around Trimble's official converter _trm2rinex_ which is not available for Linux.  
It relies on Trimble's official converter for Windows `ConvertToRinex` provided by Trimble.

The necessary software will be downloaded automatically when building the Docker image. But here are the links for information:

* [Main download page on Trimble support website](https://geospatial.trimble.com/en/support)
* [Trimble RINEX Converter](https://trl.trimble.com/docushare/dsweb/Get/Document-1080499/Trimble%20Convert%20to%20Rinex%20-%204.0.1.9%20release%20notes.pdf)
    * [Version 3.14](https://trl.trimble.com/dscgi/ds.py/Get/File-942121/convertToRinex314.msi) (the one used by the Docker)
* [Trimble Office Configuration Utility](https://trl.trimble.com/docushare/dsweb/Get/Document-1052638/022516-694%20GEO-Trimble-Office-Configuration-Utility_USL_0523.pdf) (companion software)
    * [Direct download link](https://dl.tbcrelease.net/update/config/25.4.16/TrimbleCFGUpdate.exe)

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

NB: GFZRNX usage is **not allowed** in _routine mode_ without a **proper commercial license**. Be sure to comply with it.
**The authors of _autorino_ are not responsible for any misuse of GFZRNX without license**.

### A recommended receipe for setting up the external utilities

* Create a directory for the GNSS converters in your prefered location, e.g. your `$HOME`.

```bash
mkdir /your/favorite/location/converters_gnss
cd /your/favorite/location/converters_gnss
```

* Create a subdirectory with a version name, typically the date of the download.

```bash
mkdir vYYYYMMDD
```

* Copy the GNSS converters in the version directory. Do not forget to make each of them executable with `chmod +x`


* Create a symbolic link called `operational`, pointing to the version directory.

```bash
ln -s vYYYYMMDD operational
```

* Edit your `.bashrc` or `.bash_profile` file to add the `operationnal` virtual folder to your `$PATH`, and then make
  its content available in the whole environnement.

```bash
export PATH=$PATH:/your/favorite/location/converters_gnss/operational
```

* If you want to update some conversion software, create a new version directory, set the new software inside, and
  update the `operational` symbolic link.
