## CmdInterface

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![PyPI version](https://badge.fury.io/py/cmdint.svg)](https://badge.fury.io/py/cmdint)
[![Build Status](https://travis-ci.org/MIC-DKFZ/cmdint.svg?branch=master)](https://travis-ci.org/MIC-DKFZ/cmdint)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.2562074.svg)](https://doi.org/10.5281/zenodo.2562074)

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
* Simple usage (no need to write a complicated wrapper class or something similar to run commands/functions in CmdInterface)
* Notifications via telegram messenger


#### Examples 
This is a minimal example how to log a command and what the log looks like.
 More and more complex examples can be in the [examples folder](https://github.com/MIC-DKFZ/cmdint/tree/master/examples).
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
    "cmd_interface": {
      "version": "1.2.8",
      "copyright": "Copyright 2018, German Cancer Research Center (DKFZ), Division of Medical Image Computing",
      "url": "https://github.com/MIC-DKFZ/cmdint/",
      "output": [
        "2019-02-15 11:03:38 >> ls START",
        "2019-02-15 11:03:38 >> ls END"
      ],
      "repositories": {
        "/cmdint/examples/minimal_example": {
          "autocommit": false,
          "dirty_files": [
            "Readme.md",
            "examples/minimal_example/minimal.py"
          ],
          "hash": "d77d13b1e3646d2cc47c9f00a9b0d7bf74bc2cdb"
        }
      }
    },
    "command": {
      "name": "ls",
      "is_py_function": false,
      "run_string": "ls -l ~/cmdint/",
      "return_code": 1,
      "return_code_meaning": "run successful",
      "call_stack": [
        {
          "file": "/cmdint/cmdint/CmdInterface.py",
          "line": "777",
          "function": "run"
        },
        {
          "file": "/cmdint/examples/minimal_example/minimal.py",
          "line": "13",
          "function": "<module>"
        }
      ],
      "text_output": [
        "total 40",
        "drwxr-xr-x 3 neher neher  4096 Feb 15 09:46 cmdint",
        "drwxr-xr-x 8 neher neher  4096 Feb 15 09:50 examples",
        "-rw-r--r-- 1 neher neher 11357 Feb 14 14:31 LICENSE.txt",
        ...
      ],
      "options": {
        "no_key": [],
        "key_val": {
          "-l": "~/cmdint/"
        }
      },
      "time": {
        "start": "2019-02-15 11:03:38",
        "end": "2019-02-15 11:03:38",
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
    },
    "environment": {
      "platform": {
        "system": "Linux",
        "release": "4.15.0-45-generic",
        "version": "#48-Ubuntu SMP Tue Jan 29 16:28:13 UTC 2019",
        "machine": "x86_64",
        "logical_cores": 16,
        "memory_gb": 62.77787399291992
      },
      "python": {
        "version": "3.6.7",
        "build": [
          "default",
          "Oct 22 2018 11:32:17"
        ],
        "compiler": "GCC 8.2.0",
        "implementation": "CPython",
        "imported_modules": {
          "cmdint": "1.2.8",
          "re": "2.2.1",
          ...
        },
        "pip_freeze": {
          "apturl": "0.5.2",
          "asn1crypto": "0.24.0",
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
