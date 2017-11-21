# Introduction

This package provides a script based on the python `psutil` package to run and monitorize a shell process.

The main figures of the process and its children are monitored and logged to a log file.
The script can capture the logging directory from the `logdir` parameter inside the command it's going to run.

Some of the figures enabled are:

* Max RSS (`max_rss`)
* Max VMS (`max_vms`) 
* Total I/O read and written (`total_io_read` and `total_io_write`)  
* Total CPU time (`total_cpu_time`)

The figures are logged per period and at the end of the job. Producing two different log messages:

* per period
    <pre>2017-11-21 12:46:39,813 : [INFO] - usage\_stats, max\_vms, 911.75M, max\_rss, 883.04M, total\_io\_read, 148.61M, total\_io\_write, 0B, total\_cpu\_time, 2.03</pre>
* at the end of the job
    <pre>2017-11-21 10:29:39,762 : [INFO] - usage\_stats\_summary, max\_vms, 84.45M, max\_rss, 63.05M, total\_io\_read, 17.09M, total\_io\_write, 0B, total\_cpu\_time, 0.1

Although this package can be used in any environment is has been developed to be used within the Euclid SGS infrastructure.
That is, with `euclid-ial-wfm` and `euclid-ial-drm`.

For those familiar with the Euclid SGS infrastructure, this package is not structured as an Elements package.


# Installation

Clone the PipelineUtils repository [PipelineUtils Gitlab repository](https://gitlab.euclid-sgs.uk/SDC-ES/PipelineUtils)
```
> git clone https://gitlab.euclid-sgs.uk/SDC-ES/PipelineUtils.gi
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
# if 