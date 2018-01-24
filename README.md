# Introduction

This package provides a script based on the python `psutil` package to run and monitorize a shell process.

The main figures of the process and its children are monitored and logged to a log file.
The script can capture the logging directory from the `logdir` parameter inside the command it's going to run.

Some of the figures enabled are:

* Max RSS (`max_rss`)
* Max VMS (`max_vms`) 
* Total I/O read and written (`total_io_read` and `total_io_write`)  
* Total CPU time (`total_cpu_time`)

The figures are written to a csv file at the end of each period.

Although this package can be used in any environment is has been developed to be used within the Euclid SGS infrastructure.
That is, with `euclid-ial-wfm` and `euclid-ial-drm`.

For those familiar with the Euclid SGS infrastructure, this package is not structured as an Elements package.


# Installation

Clone the PipelineUtils repository [PipelineUtils Gitlab repository](https://gitlab.euclid-sgs.uk/SDC-ES/PipelineUtils)
```
> git clone https://gitlab.euclid-sgs.uk/SDC-ES/PipelineUtils.git
```


Move to the package directory and install via the execution of the setup script. Need to have `setuptools` installed.

```
> cd PipelineUtils/run_and_monitorize
> sudo python setup.py install
```


# Usage

Run the script with the `-h` argument to see the options available:

```
> run_and_monitorize -h
usage: run_and_monitorize [-h] --command COMMAND [--conf CONF]
```

Standard usage would be:
```
    run_and_monitorize -c "{command}"
```

By default the configuration file will be picked from `/etc/run_and_monitorize/run_and_monitorize.cfg`


# Integration with IAL

In order to integrate this monitoring tool with IAL do:


in `$HOME/.ial_drm/conf.ini` add

	extra_commands_before = /path/to/some/script \</pre>

create `/path/to/some/script` with

	#!/bin/bash
	EUCLIDJOB="$@"
	/path/to/run_and_monitorize --command="$EUCLIDJOB" --conf /path/to/run_and_monitorize.cfg


# Configuration

Sample configuration file:

```
[root]
var_list=max_vms,max_rss,total_io_read,total_io_write,total_cpu_time ; list of variables to monitorize
check_lapse=0 ; time between each usage check in seconds
report_lapse=1 ; time between each usage report in seconds

[logging]
logfile=usage.log 
logdir=. 
logdir_implicit=1 ; boolean, set to True if logdir parameter is inside command to be monitorized
```

## root settings

* var_list: list of variables to be monitorized as comma-separated string. To choose among listed above.
* check and reporting period: the process figures are checked every `check_lapse` and logged every `report_lapse`. 

## Logging settings:

* logging directory: Implicit `logdir` inside command has precedence over explicit `logdir` option. If none of them exists `cwd` will be assumed as logging directory.
* log file: `logfile` or `usage.log` will be joined to logdir


# Parsing the csv usage files

Create a UsageParser instance and load the information from the usage files.

```
from var_monitor import usage_parse
parser = usage_parse.UsageParser()
parser.load_log_files(['wildcard/to/csv/files/1', ..., 'wildcard/to/csv/files/N])
```

Plot some samples:
```
parser.plot_sample(sample_size=3)
```
![sample_plot](img/sample.png)

Compute and plot some additional stats:
```
parser.plot_additional_stats()
```
![RSS hist](img/rss_hist.png)

Plot the 0%, 25%, 50%, 75% and 100% percentiles of the resources usage at each % of total time spent.
```
parser.plot_value_range()
```
![percentiles](img/percentiles.png)
