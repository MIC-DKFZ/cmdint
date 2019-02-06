## CmdInterface

Intended for people who, at some point, encountered folders with a ton of files of unknown origin that were supposedly generated during some command line or python experiment using an unknown set of parameters and who unsuccessfully tried to reproduce the results or to simply understand what happened.

To avoid such a situation, this python package enables detailed logging of command line experiments in a very lightweight manner (coding wise). Also supports logging of python functions. 
CmdInterface wraps your command line or python function calls in a few lines of code and logs everything you might need to reproduce the experiment later on or to simply check what you did a couple of years ago.

Features:
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

Examples can be found in the "examples" folder. 

Setup (python 3 required):
* pip package
    * ```pip3 install cmdint```
* Current master:
    * ```git clone https://phabricator.mitk.org/source/cmdint.git```
    * ```pip3 install -e path/to/repo/```
