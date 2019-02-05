from cmdint import CmdInterface
from pathlib import Path

'''By default, CmdInterface logs the git repository hashes of the respective last commit of two repositories:
1. the git repository of the main file that is being executed (if located in a repository)
2. the git repository of the file containing the CmdInterface class (if located in a repository)

Additonally, any other repository can be added for logging and if desired, also automatically committed if dirty.

The logged git information can be found under ['cmd_interface']['repositories'] in the json logfile
'''

# If autocommit=True, pending changes in a dirty repo are commited with an automatic commit message.
# This can be sensible since the logged commit hash otherwise does not capture the full state of the repository.
CmdInterface.add_repo_path(str(Path.home()) + '/mrtrix3/', autocommit=False)

CmdInterface.set_static_logfile('git_repository_logging.json', delete_existing=True)
test = CmdInterface('ls')
test.add_arg(key='-l', arg='/')
test.run()

CmdInterface.anonymize_log(out_log_name='git_repository_logging.json')
