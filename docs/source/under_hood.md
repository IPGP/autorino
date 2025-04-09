```{eval-rst}
.. _under_hood:
```

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

### About _epoch range_ and timing.

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
