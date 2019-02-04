from cmdint import CmdInterface
from pathlib import Path

'''Minimal example of command execution and logging with CmdInterface
'''

# create instance of CmdInterface with the name of the command to be called (here "ls")
test = CmdInterface('ls')

# add keyword based argument
test.add_arg(key='-l', arg=str(Path.home()) + '/cmdint/cmdint/')

# run command
test.run()
