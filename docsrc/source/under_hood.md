```{eval-rst}
.. _under_hood:
```

## Under the hood

_autorino_ incorporates object-oriented programming principles, with workflow steps implemented as classes. All step classes inherit from a common parent class, `StepGnss`, which provides the core functionality for handling input files and saving processed outputs.

### `StepGnss` Overview

`StepGnss` represents a single, reusable processing unit within an _autorino_ workflow. It:

- Centralizes the step state in a **table** (see below).  
- Manages site and epoch context, input/output path templating, and temporary/output directories.  
- Loads input files (from lists, directories, or previous steps), applies filters, decompresses archives, determines epochs, and infers RINEX filenames.  
- Determines required actions and skips already successful ones using `ok_inp` / `ok_out` boolean flags in the table.  
- Performs file moves/copies, size and gap validation, metadata integration, and logging (both in the table and in external log files).

#### Table Attribute

The central attribute of a `StepGnss` object is its **table** (`step_gnss.table`), implemented as a Pandas `DataFrame`. This table lists, for each epoch:

- Input files and their paths  
- Status flags (`ok_inp` / `ok_out`)  
- File sizes  
- Corresponding output files if processing was successful  

It forms the core mechanism for tracking the state of each file handled by the step.

### Subclasses of `StepGnss`

`StepGnss` has three direct subclasses:

- **`DownloadGnss`** – Downloads raw GNSS files from a remote receiver or server to a local destination.  
- **`ConvertGnss`** – Converts raw GNSS files to RINEX format.  
- **`HandleGnss`** – Performs operations such as decimation, splitting, or splicing on RINEX files. This class has three further subclasses:  
  - **`SplitGnss`** – Splits a RINEX file.  
  - **`SpliceGnss`** – Splices (concatenates) multiple RINEX files.  
  - **`ModifyGnss`** – Modifies a RINEX file (e.g., edits its header and filename); integrates the functionality of the spin-off tool `rinexmod`.

#### Execution

Each step class defines a dedicated main method, which is invoked when the step is executed. For example, the `DownloadGnss` class provides a `download()` method to perform the download operation.

## About _epoch range_ and timing.

When defining an _epoch range_ for a step, you give:
* a _first epoch_ (`epoch1`*)
* an _last epoch_ (`epoch2`*)
* a _period_ (`period`)

*: `epoch1` and `epoch2` are automatically sorted. You don't have to worry about the order, which one is the oldest 
and which one is the newest with respect to the present epoch.
 
To create an _epoch range_, autorino generates a set of (_start bound_, _end bound_) starting at the _first epoch_,
increased incrementally by the _period_, and stoped at the _ending epoch_. The _ending epoch_ is __not included__ 
as a final _start bound_.

 `epoch1` and `epoch2` can be relative epochs to the presente epoch in human-readable sentences.
(interpretation done with the [dateparser](https://github.com/scrapinghub/dateparser/) package). For instance:
* `"10 days ago"`
* `"today at 00:00"`
* `"now"`
* `"15 minutes ago"`

`epoch1` and `epoch2` can also be absolute epochs in the `date` format. For instance: `"2024-05-01 00:00:00"`

Internally, _autorino_ uses UTC timescale. (which is a good proxy for the GPS time as the minute level).
Customizing the time zone is possible by modifying the `tz` format in the configuration files.
It will change the way the input `epoch1` and `epoch2` are interpreted.
You can customize it using the [_tz database_](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
 names: e.g. `Europe/Paris`, `America/Guadeloupe`, `America/Martinique`, `Indian/Reunion` etc...

Using the `round_method` option, you can round `epoch1` and `epoch2` to the closest epoch according to `period`.
Accepted values are:
* `floor` (default): round to the closest epoch _before_ the `epoch1`/`epoch2`.
* `ceil`: round to the closest epoch _after_ the `epoch1`/`epoch2`.
* `round`: round to the closest epoch depending where you are in the period (not recommended).

### A simple exemple

If you ask on 2025-01-20 for an _epoch range_ with:
* `epoch1`: `"10 days ago"`
* `epoch2`: `"today"`
* `period`: `"01D"`
* `round_method`: `"floor"`

You will get the following results:
```commandline
        epoch_srt         epoch_end
25-01-16 00:00:00 25-01-16 23:59:59
25-01-17 00:00:00 25-01-17 23:59:59
25-01-18 00:00:00 25-01-18 23:59:59
25-01-19 00:00:00 25-01-19 23:59:59
25-01-20 00:00:00 25-01-20 23:59:59
```
