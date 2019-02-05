from cmdint import CmdInterface

# set output logfile and tell CmdInterface to delete a potentially present old logfile
CmdInterface.set_static_logfile('simple.json', delete_existing=True)

# create instance of CmdInterface with the name of the command to be called (here "ls")
test = CmdInterface('ls')

# add keyword based argument
test.add_arg(key='-l', arg='/')

# run command
test.run()

# anonymize logfile
CmdInterface.anonymize_log(out_log_name='simple.json')

# run the same command again but also print version information
# note that we don't have to set the argument again
CmdInterface.set_static_logfile('simple_with_version.json', delete_existing=True)
test.run(version_arg='--version')

# anonymize logfile
CmdInterface.anonymize_log(out_log_name='simple_with_version.json')
