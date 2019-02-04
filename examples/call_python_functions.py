from cmdint import CmdInterface
from cmdint.Utils import ProgressBar
import time


# somy dummy function to be executed using CmdInterface
def my_python_function(my_arg: str):
    for i in range(10):
        print(my_arg + ' ' + str(i))


# another dummy with progress bar
def my_python_function_with_progress():
    bar = ProgressBar(10)
    for i in range(10):
        time.sleep(1)
        bar.next()


# set output logfile and tell CmdInterface to delete a potentially present old logfile
CmdInterface.set_static_logfile('call_python_functions.json', delete_existing=True)

# create instance of CmdInterface that calls the previously defined python function "my_python_function"
test_my_python_function = CmdInterface(my_python_function)
test_my_python_function.add_arg('my_arg', 'BLABLA')
test_my_python_function.run()

# another call with our progress bar function
# the progress bar in the output logfile is updated continuously
test_my_python_function_with_progress = CmdInterface(my_python_function_with_progress)
test_my_python_function_with_progress.run()

# anonymize logfile
CmdInterface.anonymize_log(out_log_name='call_python_functions.json')
