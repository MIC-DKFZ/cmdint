from cmdint import CmdInterface
import os

# remove some files that are created in this script
if os.path.isfile('io_file_checking.txt'):
    os.remove('io_file_checking.txt')
if os.path.isfile('io_file_checking_copy.txt'):
    os.remove('io_file_checking_copy.txt')

# set output logfile and tell CmdInterface to delete a potentially present old logfile
CmdInterface.set_static_logfile('io_file_checking.json', delete_existing=True)

# we want to log if a run is not necessary. by default this is disabled since we don't want to swamp our
# logfile if we call the script multiple times
CmdInterface.set_immediate_return_on_run_not_necessary(do_return=False)

# for this example we dont't want to exit python if a run fails. default is True.
CmdInterface.set_exit_on_error(do_exit=False)

####################################################################################################
# create a new text file using "echo"
step1 = CmdInterface('echo')
step1.add_arg(arg='unus ignis quis vir multum ab audere')

# by setting "check_output" to True, the argument is regarded as an expected output file
# (logged under ['command']['output']['expected']).
# If the file is found BEFORE execution, the execution is skipped, since a run is regarded as unnecessary when all
# outputf iles are already present.
# The run fails if this file is not found AFTER execution
# (logged under: ['command']['output']['missing']).
# If it is found, the run is successful and the file hash is logged to enable unique identification
# (logged under ['command']['output']['found']).
step1.add_arg(key='>', arg='io_file_checking.txt', check_output=True)
step1.run()

####################################################################################################
# copy the previously created file using "cp"
step2 = CmdInterface('cp')
# similar to "check_output", "check_input" declares an argument as expected input file
# (logged under ['command']['input']['expected']).
# The run fails if this file is not found BEFORE execution
# (logged under: ['command']['input']['missing']).
# If it is found, the run is started and the file hash is logged to enable unique identification
# (logged under ['command']['input']['found']).
step2.add_arg(arg='io_file_checking.txt', check_input=True)
step2.add_arg(arg='io_file_checking_copy.txt', check_output=True)
step2.run()

####################################################################################################
# let's run step2 again to get a log of a skipped run since the output is already there
step2.run()

####################################################################################################
# let's create a run that will fail due to a missing input file
step3 = CmdInterface('cp')
step3.add_arg(arg='non_existing_file.txt', check_input=True)
step3.add_arg(arg='non_existing_file_copy.txt', check_output=True)
step3.run()

# anonymize logfile
CmdInterface.anonymize_log(out_log_name='io_file_checking.json')
