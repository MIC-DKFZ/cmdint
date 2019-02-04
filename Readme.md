#CmdInterface

Enables detailed logging of command line calls in a very lightweight manner (coding wise). Also supports logging of python functions. CmdInterface logs information regarding the command version, command execution, the input and output, execution times, platform and python environment information as well as git repository information.

Simple example:
```
from cmdint import CmdInterface
from pathlib import Path

# Set output logfile and tell CmdInterface to delete a potentially present old logfile
CmdInterface.set_static_logfile('simple.json', delete_existing=True)

# Create instance of CmdInterface with the name of the command to be called ("ls")
test = CmdInterface('ls')

# add keyword based argument
test.add_arg(key='-l', arg=str(Path.home()) + '/cmdint/cmdint/')

# run command
test.run()

# Anonymize logfile
CmdInterface.anonymize_log(out_log_name='simple.json')
```
