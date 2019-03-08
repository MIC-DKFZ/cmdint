from cmdint import CmdInterface
from pathlib import Path

""" Example how to call one of MITKs command line tools
"""

# Optional. We set this to change the default logfile name to mitk_example for this example script and to overwrite a
#  potentially existing old logfile instead of appending the new command line call.
CmdInterface.set_static_logfile(file='mitk_example.json', delete_existing=True)

# Convert a nrrd image file to a nifti file. Also log input and output file hashes and check if the corresponding
# files are present before or after the command execution respectively by setting check_input and check_output.
converter = CmdInterface('MitkFileFormatConverter')
converter.add_arg('-i', str(Path.home()) + '/mitk/mitkdata/brain.nrrd', check_input=True)
converter.add_arg('-o', str(Path.home()) + '/mitk/mitkdata/brain.nii.gz', check_output=True)
converter.run()

converter.anonymize_log(CmdInterface.get_static_logfile())

# If you are using a downloaded prebuilt version of MITK, call CmdInterface.set_use_installer(True) or
# directly call MitkFileFormatConverter.sh instead of MitkFileFormatConverter. set_use_installer(True) simply appends
# '.sh' to your command, which is just convenience if you frequently want to switch between installer and non installer
# versions of MITK and don't want to change all your command line calls every time. On Windows you can adjust this to
#  append '.bat': CmdInterface.set_use_installer(True, command_suffix='.bat')
