```{eval-rst}
.. _installation:
```

## Installation

### Automatic installation (recommended)

Clone the _autorino_ repository. 
```bash
git clone https://github.com/IPGP/autorino.git
```
And then install _autorino_ using the `pip` package manager. 
```bash
cd autorino
pip install .
```

For developpers, you can install _autorino_ in [developement mode](https://setuptools.pypa.io/en/latest/userguide/development_mode.html).
```bash
pip install -e .
```

### Setting up the environment

You need to set up the environment variable `$AUTORINO_ENV` to point to the _autorino_'s configuration file.

In your `.bashrc` or `.bash_profile` file, add the following lines:
```bash
export AUTORINO_ENV="/home/user/path_to/autorino/configfiles/env/autorino_env.yml"
```
This configuration file is a YAML file that contains the paths to the different GNSS raw data converters, described in the next section below.

If `$AUTORINO_ENV` is not set, _autorino_ will use the default configuration file located in the package's `configfiles/env/` folder.  
Per defaults values assume that the converter executables are known by your system and (e.g. set in your `$PATH`).
