## CmdInterface

Copyright © German Cancer Research Center (DKFZ), [Division of Medical Image Computing (MIC)](https://www.dkfz.de/en/mic/index.php). Please make sure that your usage of this code is in compliance with the code [license](https://github.com/MIC-DKFZ/cmdint/blob/master/LICENSE.txt).

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![PyPI version](https://badge.fury.io/py/cmdint.svg)](https://badge.fury.io/py/cmdint)
[![Build Status](https://travis-ci.org/MIC-DKFZ/cmdint.svg?branch=master)](https://travis-ci.org/MIC-DKFZ/cmdint)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.2633770.svg)](https://doi.org/10.5281/zenodo.2633770)

Intended for people who, at some point, encountered folders with a ton of files of unknown origin that were supposedly generated during some command line or python experiment using an unknown set of parameters and who unsuccessfully tried to reproduce the results or to simply understand what happened.

To avoid such a situation, this python package enables detailed logging of command line experiments in a very lightweight manner (coding wise). Also supports logging of python functions. 
CmdInterface wraps your command line or python function calls in a few lines of code and logs everything you might need to reproduce the experiment later on or to simply check what you did a couple of years ago.

* [Features](#Features)
* [Examples](#Examples)
* [Installation](#Installation)

#### Features:
* Logged information as json file:
    * Executed command line or python function call as string
    * Command output (stdout + stderr)
    * Command parameters
    * Command version
    * Command call stack
    * Input and output file hashes
    * Execution times
    * Git repository information
    * Platform information (operating system, version, number of cpus, memory, ...)
    * Python information (version, modules, ...)
* Optional tarbal archiving of touched pyhon files
* Simple usage (no need to write a complicated wrapper class or something similar to run commands/functions in CmdInterface)
* Notifications via telegram or slack messenger


#### Examples 
This is a minimal example how to log a command and what the log looks like.
 More and more complex examples can be found in the [examples folder](https://github.com/MIC-DKFZ/cmdint/tree/master/examples).
```
# Import our logging module
from cmdint import CmdInterface

# create instance of CmdInterface with the name of the command to be called (here "ls")
test = CmdInterface('ls')

# add keyword based argument
test.add_arg(key='-l', arg='~/cmdint/')

# run command
test.run()
```
Logged information (a bit shortened):

```
[
  {
    "run_id": "1588bb37-2eaa-4313-8aba-21a6d339e13b",
    "tracked_repositories": {
      "/coding/cmdint/examples/minimal_example": {
        "autocommit": false,
        "dirty_files": [
          "examples/minimal_example/minimal.py"
        ],
        "hash": "bf71f45887ca0e2949d64e79e8ec3909e64cf829"
      }
    },
    "source_tarball": null,
    "cmdint": {
      "version": "3.0.0",
      "copyright": "Copyright 2018, German Cancer Research Center (DKFZ), Division of Medical Image Computing",
      "url": "https://github.com/MIC-DKFZ/cmdint/",
      "output": [
        [
          "2020-02-19 11:35:28",
          "ls START"
        ],
        [
          "2020-02-19 11:35:29",
          "ls END"
        ]
      ]
    },
    "commands": [
      {
        "name": "ls",
        "is_py_function": false,
        "description": null,
        "run_string": "ls -l",
        "return_code": 1,
        "return_code_meaning": "run successful",
        "call_stack": [
          {
            "file": "/coding/cmdint/cmdint/CmdInterface.py",
            "line": "1007",
            "function": "run"
          },
          {
            "file": "/coding/cmdint/examples/minimal_example/minimal.py",
            "line": "13",
            "function": "<module>"
          }
        ],
        "text_output": [
          "total 20",
          "-rw-r--r-- 1 neher neher 9235 Feb 19 11:35 CmdInterface.json",
          "-rw-r--r-- 1 neher neher 2806 Nov 29 11:17 minimal.ipynb",
          "-rw-r--r-- 1 neher neher  331 Feb 19 11:35 minimal.py"
        ],
        "options": {
          "no_key": [],
          "key_val": {
            "-l": "None"
          }
        },
        "time": {
          "start": "2020-02-19 11:35:28",
          "end": "2020-02-19 11:35:29",
          "duration": "0:00:00",
          "utc_offset": 3600
        },
        "input": {
          "expected": [],
          "found": [],
          "missing": []
        },
        "output": {
          "expected": [],
          "found": [],
          "missing": []
        }
      }
    ],
    "environment": {
      "platform": {
        "system": "Linux",
        "release": "5.3.0-29-generic",
        "version": "#31-Ubuntu SMP Fri Jan 17 17:27:26 UTC 2020",
        "machine": "x86_64",
        "logical_cores": 16,
        "memory_gb": 62.680545806884766
      },
      "python": {
        "version": "3.7.5",
        "build": [
          "default",
          "Nov 20 2019 09:21:52"
        ],
        "compiler": "GCC 9.2.1 20191008",
        "implementation": "CPython",
        "imported_modules": {
          "cmdint": "3.0.0",
          "re": "2.2.1",
          ...
        },
        "pip_freeze": {
          "aiohttp": "3.6.2",
          "apturl": "0.5.2",
          "argparse": "1.4.0",
          ...
        }
      }
    }
  }
]
```

#### Installation 
Python 3 required!
* pip package
    * ```pip3 install cmdint```
* Current master variant 1:
    * ```pip3 install https://github.com/MIC-DKFZ/cmdint/archive/master.zip```
* Current master variant 2:
    * ```git clone https://phabricator.mitk.org/source/cmdint.git```
    * ```pip3 install -e path/to/repo/```
