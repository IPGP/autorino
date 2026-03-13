```{eval-rst}
.. _config_files_details:
```

# Configuration file details

## Configuration File Structure

### 1. `cfgfile_version`
- **Purpose**: Specifies the version of the configuration file format.
- **Example**: `cfgfile_version: 20.1`

### 2. `environment`
Defines global settings for the GNSS data processing environment, including paths to software tools and general application settings.

#### Subsections:
- **`conv_software_paths`**: Specifies paths to GNSS raw data converters.
  - **Keys**:
    - `convbin`: Path to RTKLIB converter.
    - `mdb2rinex`: Path to Leica converter.
    - `sbf2rin`: Path to Septentrio converter.
    - `tps2rin`: Path to Topcon converter.
    - `t0xconvert`: Path to Trimble official converter.
    - `trm2rinex`: Path to Trimble unofficial docker converter.
    - `runpkr00`: Path to Trimble legacy converter for TEQC.
    - `converto`: Path to ConvertoCPP tool.
    - `gfzrnx`: Path to GFZRNX tool.
    - `teqc`: Path to TEQC tool.
- **`general`**:
  - `log_level`: Logging verbosity (e.g., `DEBUG`, `INFO`).
  - `trimble_default_software`: Default Trimble converter to use (e.g., `trm2rinex`).
  - `cfg_merge_strategy`: Strategy for merging configuration files (`replace` or `additive`).

### 3. `station`
Contains station-specific information and configuration.

#### Subsections:
- **`site`**: Metadata about the site.
  - **Keys**:
    - `operator`: Name of the site operator.
    - `agency`: Name of the managing agency.
    - `country`: Country name in ISO 3166 format.
    - `sitelog_path`: Path to site logs (file or directory).
    - `name`: 'Your Site Full Free Name' # Your Site Full Free Name
    - `site_id`: Your Site 9-char. code
    - `domes`: Your Site DOMES number
    - `position_xyz`: Your Site approximate coordinates in ECEF (X, Y, Z) in meters
- **`access`**: Connection protocols, login credentials, etc.
  - **Keys**:
    - `protocol`: The protocol to access the data (`ftp` or `http`).
    - `hostname`: IP address or URL to access the remote receiver/server
    - `login`: login username
    - `password`: login password
    - `datalink`: a free keyword to prevent download of several stations with the same datalink at the same time
- **`device`**: Manually defines the device's (receiver and antenna) characteristics
  - **Keys**: 
    - `attributes_from_sitelog`: Choose if the device attribute will come from a sitelog given with `sitelog_path` or the values below
    - `ant_type`: Antenna type from code IGS code files https://files.igs.org/pub/station/general/rcvr_ant.tab
    - `ant_sn`:  Antenna Serial Number
    - `ecc_une`:  Eccentricity Up North East of the antenna reference point in meters
    - `rec_type`: Receiver type from code IGS code files https://files.igs.org/pub/station/general/rcvr_ant.tab
    - `rec_sn`: Receiver Serial Number
    - `rec_fw`: Receiver firmware version
- **`sessions`**: Defines the characteristics of recording sessions.

### 4. `sessions`
Each session is defined under a `session_<sessionname>` block. It includes the following:

#### Subsections:
- **`general`**: General session settings.
  - **Keys**:
    - `active`: Boolean indicating if the session is active.
    - `name`: Name of the session. 
    - `tmp_dir_parent`: Parent directory for temporary files.
    - `tmp_dir_structure`: Directory structure for temporary files.
    - `log_dir_parent`: Parent directory for log files.
    - `log_dir_structure`: Directory structure for log files.
- **`epoch_range`**: Time range for the session.
  - **Keys**:
    - `epoch1`: Start of the epoch range (e.g., `10 days ago UTC`).
    - `epoch2`: End of the epoch range (e.g., `yesterday at 23:59 UTC`).
    - `period`: Time period using Pandas offset aliases (e.g., `1D`).
    - `round_method`: Method to round timestamps (e.g., `floor`).
    - `tz`: Timezone for the session (e.g., `UTC`).
- **`steps`**: Workflow steps for the session.

### 5. Workflow Steps
Each step represents a specific operation in the workflow (e.g., `download`, `convert`, `splice`, `split`).

#### Generic Step Structure:
- **Keys**:
  - `active`: Boolean to enable or disable the step.
  - `inp_dir_parent`: Parent directory for input files.
  - `inp_dir_structure`: Directory structure for input files.
  - `out_dir_parent`: Parent directory for output files.
  - `out_dir_structure`: Directory structure for output files.
  - `epoch_range`: Time range for the step (can use `FROM_SESSION`).
  - `options`: Step-specific options.

#### Example Steps:
- **`download`**: Downloads GNSS data.
  - **Options**:
    - `force`: Force re-download of files.
    - `remote_find_method`: Method to find remote files (`ask` or `guess`).
    - `invalidate_small_local_files`: Invalidate small local files (smaller than few kB) and force their download.
    - `timeout`: Timeout for remote connections in seconds.
    - `max_try`: Maximum number of retries for remote connections.
    - `sleep_time`: Sleep time between retries in seconds.
    - `ping_timeout`: Timeout for pinging remote servers in seconds.
    - `ping_max_try`: Maximum number of ping retries.
- **`convert`**: Converts raw GNSS data to RINEX format.
  - **Options**:
    - `force`: Force re-conversion of files.
    - `converter`: Converter to use (e.g., `auto`).
    - `conv_regex_custom_main`: custom regex to catch converted temporary main file.
    - `conv_regex_custom_annex`: Custom regex to catch converted temporary annex files.
    - `rinexmod_options`: 
      - `compression`: Compression format for RINEX files (e.g., `gz`).
      - `longname`: Use long file names.
      - `force_rnx_load`: Force loading of RINEX files.
      - `verbose`: Enable verbose output.
      - `filename_style`: Style for file names (e.g., `basic`).
      - `full_history`: Keep full history of operations.
      - See [_rinexmod_ API documentation](https://github.com/IPGP/rinexmod/blob/master/README.md) for details.

### 6. Aliases
Aliases allow dynamic values in the configuration files. Examples:
- `<site_id4>`: 4-character site name in lower case.
- `<site_id9>`: 9-character site name in lower case.
- `<SITE_ID4>`: 4-character site name in upper case.
- `<SITE_ID9>`: 9-character site name in upper case.
- `<$HOME>`: Environment variable for the home directory.
- Time-based aliases (e.g., `%Y` for year, `%j` for day of year).

### 7. Reserved Keywords
- `FROM_SESSION`: Inherits values from the session block.

## Notes
- Configuration files are modular and can be merged using the `cfg_merge_strategy`.
- Default values are assumed if certain parameters are not explicitly defined.
