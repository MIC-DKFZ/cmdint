import os
import subprocess
from datetime import datetime
import time
import git
import hashlib
import sys
import inspect
import json
import io
import chardet
import telegram
from pathlib import Path
from shutil import which
from cmdint.Utils import *


class CmdInterface:
    """
    Enables detailed logging of command line calls in a very lightweight manner (coding wise). Also supports logging of
    python functions. CmdInterface logs information regarding the command version, command execution, the input and
    output, execution times, platform and python environment information as well as git repository information.
    """

    # private
    __logfile_name: str = 'CmdInterface.json'
    __git_repos: dict = dict()
    __return_code_meanings: dict = {0: 'not run',
                                    1: 'run successful',
                                    2: 'run not necessary',
                                    -1: 'output missing after run',
                                    -2: 'input missing',
                                    -3: 'exception'}
    __use_installer: bool = False
    __autocommit_mainfile_repo: bool = False
    __autocommit_mainfile_repo_done: bool = False
    __immediate_return_on_run_not_necessary: bool = True
    __exit_on_error: bool = False
    __throw_on_error: bool = True
    __installer_replacements: list = list()
    __installer_command_suffix: str = '.sh'
    __print_messages: bool = True
    __called: bool = False  # check for recoursion

    # telegram logging
    __token: str = None
    __chat_id: str = None
    __bot: telegram.Bot = None
    __caption: str = None
    __send_start: bool = True
    __send_end: bool = True
    __send_log: bool = True

    def __init__(self, command, static_logfile: str = None):
        """
        Create new instance of CmdInterface with the command or python function as parameter.
        """
        self.__check_input = list()
        self.__check_output = list()

        if static_logfile is not None:
            CmdInterface.set_static_logfile(static_logfile)

        CmdInterface.__auto_add_repo_path()

        self.__log = CmdLog()
        self.__options = dict()
        self.__no_key_options = [command]

        self.__is_py_function = callable(command)
        self.__py_function_return = None

        self.__nested = False
        self.__no_new_log = False
        self.__ignore_cmd_retval = False
        self.__silent = False

        if not self.__is_py_function:
            command = command.strip()
            if CmdInterface.__use_installer:
                command += CmdInterface.__installer_command_suffix
            if len(command) == 0 or which(command) is None:
                print('Command not found: ' + command)
                raise OSError('Command not found: ' + command)

        if not self.__is_py_function and self.__no_key_options[0][:4] == 'Mitk':
            self.add_arg('--version')

    def set_ignore_cmd_retval(self, do_ignore: bool):
        """ if True, the return value of command line calls is ignored. Default is False. In this case,
        an exception is triggered if the return value is not 0.
        """
        self.__ignore_cmd_retval = do_ignore

    @staticmethod
    def set_print_messages(do_print: bool):
        """ if True, every logged message (log_message()) is also printed to stdout. Default is True.
        """
        CmdInterface.__print_messages = do_print

    @staticmethod
    def set_exit_on_error(do_exit: bool):
        """ if True, CmdInterface calls exit() if an error is encountered. Default is False.
        """
        CmdInterface.__exit_on_error = do_exit

    @staticmethod
    def set_throw_on_error(do_throw: bool):
        """ if True, CmdInterface throws exception if an error is encountered. Default is True.
        """
        CmdInterface.__throw_on_error = do_throw

    @staticmethod
    def set_immediate_return_on_run_not_necessary(do_return: bool):
        """ If True, immediatly return without any logging when all outputs are found and running the command is
        therefore  not necessary. Otherwise add this information to the log. Default is True.
        """
        CmdInterface.__immediate_return_on_run_not_necessary = do_return

    @staticmethod
    def set_telegram_logger(token: str,
                            chat_id: str,
                            caption: str = None,
                            send_start_message: bool = True,
                            send_end_message: bool = True,
                            send_log_on_end: bool = True):
        """
        Receive telegram messages of your CmdInterface runs. How to get a token and chat_id:
        https://github.com/python-telegram-bot/python-telegram-bot/wiki/Introduction-to-the-API
        """
        if token is None or chat_id is None:
            CmdInterface.__token = None
            CmdInterface.__chat_id = None
            CmdInterface. __bot = None
            CmdInterface.__caption = None
            CmdInterface.__send_start = True
            CmdInterface.__send_end = True
            CmdInterface.__send_log = True
        else:
            CmdInterface.__token = token
            CmdInterface.__chat_id = chat_id
            CmdInterface.__bot = telegram.Bot(token=CmdInterface.__token)
            CmdInterface.__caption = caption
            CmdInterface.__send_start = send_start_message
            CmdInterface.__send_end = send_end_message
            CmdInterface.__send_log = send_log_on_end

    @staticmethod
    def send_telegram_message(message: str):
        """
        Send message to the previously specified chat_id.
        """
        if CmdInterface.__bot is not None:
            try:
                if CmdInterface.__caption is not None:
                    message = CmdInterface.__caption + ":\n" + message
                CmdInterface.__bot.send_message(chat_id=CmdInterface.__chat_id, text=message)
            except Exception as err:
                print("Could not send message to telegram: " + str(err))

    @staticmethod
    def send_telegram_logfile(message: str = None):
        """
        Send logfile to the previously specified chat_id.
        """
        if CmdInterface.__bot is not None and os.path.isfile(CmdInterface.__logfile_name):
            try:
                text = None
                if CmdInterface.__caption is not None:
                    text = CmdInterface.__caption
                if message is not None:
                    if text is None:
                        text = message
                    else:
                        text += '\n' + message
                CmdInterface.__bot.send_document(chat_id=CmdInterface.__chat_id,
                                                 document=open(CmdInterface.__logfile_name, 'rb'),
                                                 caption=text)
            except Exception as err:
                print("Could not send file to telegram: " + str(err))

    @staticmethod
    def get_static_logfile() -> str:
        """
        Return current logfile path.
        """
        return CmdInterface.__logfile_name

    @staticmethod
    def set_static_logfile(file: str, delete_existing: bool = False):
        """
        Set logfile path. Logfiles are stored in json format. Existing logfiles are appended if not specified otherwise.
        If the file does not exist, a new one is created automatically.
        Each toplevel entry of a logfile corresponds to one execution of CmdInterface.run
        """
        if CmdInterface.__called:
            print('Nested CmdInterface usage. Logfile not set.')
            return
        CmdInterface.__logfile_name = file
        if file is None:
            return
        if delete_existing and os.path.isfile(CmdInterface.__logfile_name):
            os.remove(CmdInterface.__logfile_name)
        if os.path.dirname(file) != '':
            os.makedirs(os.path.dirname(file), exist_ok=True)

    @staticmethod
    def check_exist(expected_files_folders: list) -> list:
        """
        Check if the file paths in the input list indicate existing files.  Return list of missing files.
        """
        missing = list()
        for f in expected_files_folders:
            if isinstance(f, list):
                missing += CmdInterface.check_exist(f)
            elif not os.path.isfile(str(f)) and not os.path.isdir(str(f)):
                missing.append(str(f))
        return missing

    @staticmethod
    def set_autocommit_mainfile_repo(do_autocommit: bool):
        """ If True, the automatically determined git repository of the main file currently being executed is commited
        if dirty. Default is False.
        """
        CmdInterface.__autocommit_mainfile_repo = do_autocommit
        CmdInterface.__autocommit_mainfile_repo_done = False

    @staticmethod
    def __auto_add_repo_path():
        """
        Add path to git repository of current main file. CmdInterface logs the current git commit hash of this
        repository.
        """
        if CmdInterface.__autocommit_mainfile_repo_done:
            return
        path = os.path.dirname(os.path.abspath(inspect.stack()[-1][1]))
        try:
            git.Repo(path=path, search_parent_directories=True)
            CmdInterface.add_repo_path(path, autocommit=CmdInterface.__autocommit_mainfile_repo)
        except:
            pass
        path = os.path.dirname(__file__)
        try:
            git.Repo(path=path, search_parent_directories=True)
            CmdInterface.add_repo_path(path, autocommit=False)
        except:
            pass
        CmdInterface.__autocommit_mainfile_repo_done = True

    @staticmethod
    def add_repo_path(path: str, autocommit: bool = False):
        """
        Add path to git repository. CmdInterface logs the current git commit hash of this repository.
        If not disabled, pending changes in a dirty repo are commited with an automatic commit message. This is
        sensible since the logged commit hash otherwise does not capture the full state of the repository.
        """
        if os.path.isdir(path):
            git.Repo(path=path, search_parent_directories=True)
            CmdInterface.__git_repos[path] = dict()
            CmdInterface.__git_repos[path]['autocommit'] = autocommit
            CmdInterface.__check_repo(path)
        else:
            print('"' + path + '" is not a directory')
            raise NotADirectoryError('"' + path + '" is not a directory')

    @staticmethod
    def remove_repo_path(path: str):
        """
        Remove path to git repository from CmdInterface.
        """
        if path in CmdInterface.__git_repos.keys():
            del CmdInterface.__git_repos[path]

    @staticmethod
    def __check_repo(repo_path: str):
        """
        Automatically called when a git repository path is set.
        Check if the repository is dirty and commit if necessary.
        """
        try:
            CmdInterface.__git_repos[repo_path]['dirty_files'] = []
            repo = git.Repo(path=repo_path, search_parent_directories=True)
            if repo.is_dirty() and CmdInterface.__git_repos[repo_path]['autocommit']:
                print('Repo ' + repo_path + ' is dirty. Committing changes.')
                repo.git.add('-u')
                repo.index.commit('CmdInterface automatic commit')
                print('git commit hash: ' + repo.head.object.hexsha)
            elif repo.is_dirty():
                CmdInterface.__git_repos[repo_path]['dirty_files'] = [item.a_path for item in repo.index.diff(None)]
                print('Warning, repo ' + repo_path + ' is dirty!')
            CmdInterface.__git_repos[repo_path]['hash'] = repo.head.object.hexsha
            CmdInterface.__git_repos[repo_path]['autocommit'] = CmdInterface.__git_repos[repo_path]['autocommit']
        except Exception as err:
            print('Exception: ' + str(err))
            CmdInterface.__git_repos[repo_path]['exception'] = str(err)

    def get_py_function_return(self):
        """
        Return the output of the pathon function executed with this instance of CmdInterface. Returns None if the
        command is not a python function, if the execution was not successful or if it has not been not executed yet.
        """
        return self.__py_function_return

    def remove_arg(self, key: str):
        """
        Remove argument previously added with add_arg. The argument is identified by it's key.
        Arguments without key cannot be removed. Create a new instance CmdInterface in this case.
        """
        key = str(key)
        if key in self.__options.keys():
            if self.__options[key] in self.__check_input:
                self.__check_input.remove(self.__options[key])
            if self.__options[key] in self.__check_output:
                self.__check_output.remove(self.__options[key])
            del self.__options[key]
        else:
            print('No argument with specified keyword found! Arguments without keyword cannot be removed. '
                  'Create a new instance of CmdInterface in this case.')
            raise ValueError('No argument with specified keyword found! Arguments without keyword cannot be removed. '
                             'Create a new instance of CmdInterface in this case.')

    def add_arg(self,
                key: str = None,
                arg=None,
                check_input: bool = False,
                check_output: bool = False):
        """
        Add argument of the tool/function to be executed. Python functions only support arguments WITH keyword here!

        check_input: if True, this argument is regarded as an input file path. Before running the command,
                     CmdInterface checks if this file actually exists and returns an error otherwise.

        check_output: if True, this argument is regarded as an output file path. Before running the command,
                      CmdInterface checks if a run is necessary or if all output files are already present.
                      After running the command, CmdInterface checks if all files marked as output can be
                      found and returns an error if this is not the case.
        """
        if key is None and arg is None:
            return
        if self.__is_py_function:
            if key is None:
                print('Only arguments with keyword are allowed when executing python functions!')
                raise ValueError('Only arguments with keyword are allowed when executing python functions!')

        if check_input:
            self.__check_input.append(arg)
        if check_output:
            self.__check_output.append(arg)

        if key is None:
            self.__no_key_options.append(arg)
        else:
            self.__options[str(key)] = arg

    @staticmethod
    def __stringify_arg(key, arg) -> str:
        """
        Convert command line option to string, which is needed to assemble the final command string.
        """
        if isinstance(arg, list):
            arg = ' '.join(str(x) for x in arg)
        else:
            arg = str(arg)
        if key is None:
            arg = ' ' + arg
        return arg

    def get_run_string(self) -> str:
        """
        Assemble and return the command string that is going to be passed as shell command to subprocess.
        """
        if self.__is_py_function:
            run_string = str(self.__no_key_options[0].__name__) + '('
            keys = list(self.__options.keys())
            for key in keys:
                run_string += str(key) + '=' + str(self.__options[key])
                if key != keys[-1]:
                    run_string += ', '
            run_string += ')'
            return run_string

        run_string = str(self.__no_key_options[0])
        if CmdInterface.__use_installer:
            run_string += CmdInterface.__installer_command_suffix

        for el in self.__no_key_options[1:]:
            run_string += self.__stringify_arg(key=None, arg=el)

        for key in self.__options.keys():
            run_string += ' ' + key
            if self.__options[key] is not None:
                run_string += ' ' + self.__stringify_arg(key=key, arg=self.__options[key])

        if CmdInterface.__use_installer:
            for rep in CmdInterface.__installer_replacements:
                run_string = run_string.replace(rep[0], rep[1])

        return run_string

    @staticmethod
    def __jsonable(input):
        """
        Stringify everything that is not dict or list.
        """
        if isinstance(input, dict):
            out = dict()
            for key in input.keys():
                out[str(key)] = CmdInterface.__jsonable(input[key])
            return out
        elif isinstance(input, list):
            out = list()
            for el in input:
                out.append(CmdInterface.__jsonable(el))
            return out
        else:
            return str(input)

    @staticmethod
    def set_use_installer(use_installer: bool, command_suffix: str = '.sh'):
        """
        Causes the CmdInterface to automatically append the specifed suffix to your command line tool.
        This is only sensible in certain cases, such as when switching between the installer and non-installer version
        of MITK Diffusion cmdapps. In this case you would't want to always change all CmdInterface instances but simply
        set this flag.
        """
        CmdInterface.__use_installer = use_installer
        CmdInterface.__installer_command_suffix = command_suffix

    @staticmethod
    def add_installer_replacement(v1: str, v2: str):
        """
        Simple string replacement in the command to be executed, This replacement is performed only if
        set_use_installer has been set to True.
        """
        CmdInterface.__installer_replacements.append((str(v1), str(v2)))

    @staticmethod
    def get_file_hashes(files: list) -> list:
        """
        Iterate over the input list of filen paths and obtain MD5 hashes of these files.
        Return list of tuples (file path, hash).
        """
        blocksize = 65536
        hasher = hashlib.md5()
        out = list()
        for file in files:
            if isinstance(file, list):
                out += CmdInterface.get_file_hashes(file)
                continue
            if not os.path.isfile(file):
                if os.path.isdir(file):
                    out.append((file, 'folder'))
                continue
            with open(file, 'rb') as afile:
                buf = afile.read(blocksize)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = afile.read(blocksize)
                out.append((file, hasher.hexdigest()))
        return out

    def __log_start(self) -> datetime:
        """
        Log start time and timezone (UTC offset in seconds) of command execution:
        ['command']['time']['start']
        ['command']['time']['utc_offset']
        Return start time.
        """
        self.__log['command']['call_stack'] = list()
        for frame in inspect.stack()[1:]:
            el = dict()
            el['file'] = os.path.abspath(str(frame[1]))
            el['line'] = str(frame[2])
            el['function'] = str(frame[3])
            self.__log['command']['call_stack'].append(el)

        start_time = datetime.now()
        self.__log['command']['time']['start'] = start_time.strftime("%Y-%m-%d %H:%M:%S")
        self.__log['command']['time']['utc_offset'] = time.localtime().tm_gmtoff
        self.log_message(start_time.strftime("%Y-%m-%d %H:%M:%S") + ' >> ' + self.__log['command']['name'] + ' START')
        if CmdInterface.__send_start and not self.__silent:
            CmdInterface.send_telegram_message('START ' + self.__log['command']['name'])
        return start_time

    def __log_end(self, start_time: datetime, return_code: int) -> datetime:
        """
        Log end time and duration of command execution:
        ['command']['time']['end']
        ['command']['time']['duration']
        Return end time.
        """

        # set times
        end_time = datetime.now()
        self.__log['command']['time']['end'] = end_time.strftime("%Y-%m-%d %H:%M:%S")

        if start_time is None:
            return
        duration = end_time - start_time
        hours, remainder = divmod(duration.seconds, 3600)
        hours += duration.days * 24
        minutes, seconds = divmod(remainder, 60)
        duration_formatted = '%d:%02d:%02d' % (hours, minutes, seconds)
        self.__log['command']['time']['duration'] = duration_formatted

        # log end messages & return code
        self.log_message(end_time.strftime("%Y-%m-%d %H:%M:%S") + ' >> ' + self.__log['command']['name'] + ' END')
        if (CmdInterface.__throw_on_error or CmdInterface.__exit_on_error) and return_code <= 0:
            self.log_message('Exiting due to error: ' + self.__return_code_meanings[return_code])
        self.__log['command']['return_code'] = return_code
        self.update_log()

        if not self.__silent:
            if CmdInterface.__send_log:
                CmdInterface.send_telegram_logfile(
                    message='END ' + self.__log['command']['name'] + '\n' + self.__return_code_meanings[return_code])
            elif CmdInterface.__send_end:
                CmdInterface.send_telegram_message(
                    message='END ' + self.__log['command']['name'] + '\n' + self.__return_code_meanings[return_code])

        return end_time

    def log_message(self, message: str, via_telegram: bool = False):
        """
        Store string in log (['cmd_interface']['output']).
        """
        message = str(message)
        if CmdInterface.__print_messages:
            print(message)
        self.__log['cmd_interface']['output'].append(message)
        if via_telegram:
            CmdInterface.send_telegram_message(message)

    def __pyfunction_to_log(self):
        """
        Run python function and store terminal output in log (['command']['text_output']).
        """
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = sys.stderr = out_string = io.StringIO()

        if self.__silent:

            try:
                self.__no_key_options[0](*self.__no_key_options[1:], **self.__options)
            except Exception:
                sys.stdout = original_stdout
                sys.stderr = original_stderr
                raise
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            return

        try:
            proc = ThreadWithReturn(target=self.__no_key_options[0],
                                    args=self.__no_key_options[1:],
                                    kwargs=self.__options)
            proc.start()
            while proc.is_alive():
                if self.__nested:
                    print(out_string.getvalue(), end='')
                else:
                    self.__log['command']['text_output'] = out_string.getvalue().split('\n')
                    self.update_log()
                    time.sleep(5)
            self.__py_function_return, exception = proc.get_retval()

        except Exception as err:
            exception = err
        sys.stdout = original_stdout
        sys.stderr = original_stderr

        if self.__nested:
            print(out_string.getvalue(), end='')
        else:
            self.__log['command']['text_output'] = out_string.getvalue().split('\n')
            self.update_log()

        if exception is not None:
            raise exception

    def __cmd_to_log(self, run_string: str, version_arg: str = None):
        """
        Run command line tool and store output in log.
        """
        if self.__silent:
            retval = subprocess.call(run_string,
                                     shell=True,
                                     stdout=open(os.devnull, 'wb'),
                                     stderr=open(os.devnull, 'wb'))
            if retval != 0:
                raise OSError(retval, 'Command line subprocess return value is ' + str(retval))
            return

        # print version argument if using MITK cmd app or if version arg is specified explicitely
        if version_arg is not None:
            self.__log['command']['text_output'].append('')
            start_time = datetime.now()
            proc = subprocess.Popen(self.__no_key_options[0] + ' ' + version_arg,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT)
            while proc.poll() is None:
                c = proc.stdout.read(1)
                if c is None:
                    continue
                encoding = chardet.detect(c)['encoding']
                if encoding is None:
                    continue
                c = str(c.decode(encoding))
                if self.__nested:
                    print(c, end='')
                else:
                    if c == os.linesep or c == '\r':
                        self.__log['command']['text_output'].append('')
                    else:
                        self.__log['command']['text_output'][-1] += c
                        if (datetime.now() - start_time).seconds > 5:
                            start_time = datetime.now()
                            self.update_log()
            res_out = proc.stdout.read()
            encoding = chardet.detect(res_out)['encoding']
            res_out = str(res_out.decode(encoding))
            if self.__nested:
                print(res_out, end='')
            else:
                if res_out[:2] != os.linesep:
                    temp = res_out.splitlines()
                    self.__log['command']['text_output'][-1] += temp[0]
                    if len(temp) > 1:
                        self.__log['command']['text_output'] += temp[1:]
                else:
                    self.__log['command']['text_output'] += res_out.splitlines()
                self.update_log()

        self.__log['command']['text_output'].append('')
        start_time = datetime.now()
        proc = subprocess.Popen(run_string,
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        while proc.poll() is None:
            c = proc.stdout.read(1)
            if c is None:
                continue
            encoding = chardet.detect(c)['encoding']
            if encoding is None:
                continue
            c = str(c.decode(encoding))
            if self.__nested:
                print(c, end='')
            else:
                if c == os.linesep or c == '\r':
                    self.__log['command']['text_output'].append('')
                else:
                    self.__log['command']['text_output'][-1] += c
                    if (datetime.now() - start_time).seconds > 5:
                        start_time = datetime.now()
                        self.update_log()

        res_out = proc.stdout.read()
        if res_out is None:
            return
        encoding = chardet.detect(res_out)['encoding']
        if encoding is None:
            return
        res_out = str(res_out.decode(encoding))

        if self.__nested:
            print(res_out, end='')
        else:
            if res_out[:2] != os.linesep:
                temp = res_out.splitlines()
                self.__log['command']['text_output'][-1] += temp[0]
                if len(temp) > 1:
                    self.__log['command']['text_output'] += temp[1:]
            else:
                self.__log['command']['text_output'] += res_out.splitlines()
            self.update_log()

        if proc.returncode != 0 and not self.__ignore_cmd_retval:
            raise OSError(proc.returncode, 'Command line subprocess return value is ' + str(proc.returncode))

    def update_log(self):
        """
        Replace last entry of the json logfile by log of current instance.
        """
        if CmdInterface.__logfile_name is None or self.__no_new_log:
            return
        self.__log['command']['return_code_meaning'] = self.__return_code_meanings[self.__log['command']['return_code']]
        self.__log['cmd_interface']['repositories'] = CmdInterface.__git_repos
        self.__log['command']['options']['no_key'] = CmdInterface.__jsonable(self.__no_key_options[1:])
        self.__log['command']['options']['key_val'] = CmdInterface.__jsonable(self.__options)
        data = list()
        if os.path.isfile(CmdInterface.__logfile_name):
            with open(CmdInterface.__logfile_name) as f:
                data = json.load(f)
        if len(data) == 0:
            data.append(self.__log)
        else:
            data[-1] = self.__log
        with open(CmdInterface.__logfile_name, 'w') as f:
            json.dump(data, f, indent=2, sort_keys=False)

    def append_log(self):
        """
        Append log of current instance to the output json file. Creates new json if it does not exist.
        """
        if CmdInterface.__logfile_name is None or self.__no_new_log:
            return
        self.__log['command']['return_code_meaning'] = self.__return_code_meanings[self.__log['command']['return_code']]
        self.__log['cmd_interface']['repositories'] = CmdInterface.__git_repos
        self.__log['command']['options']['no_key'] = CmdInterface.__jsonable(self.__no_key_options[1:])
        self.__log['command']['options']['key_val'] = CmdInterface.__jsonable(self.__options)
        data = list()
        if os.path.isfile(CmdInterface.__logfile_name):
            with open(CmdInterface.__logfile_name) as f:
                data = json.load(f)
        data.append(self.__log)
        with open(CmdInterface.__logfile_name, 'w') as f:
            json.dump(data, f, indent=2, sort_keys=False)

    @staticmethod
    def load_log() -> list:
        """
        Load the current json logfile and return as list of dicts.
        """
        if CmdInterface.__logfile_name is None or not os.path.isfile(CmdInterface.__logfile_name):
            return None

        log = list()
        if os.path.isfile(CmdInterface.__logfile_name):
            with open(CmdInterface.__logfile_name) as f:
                log = json.load(f)

        return log

    @staticmethod
    def anonymize_log(out_log_name: str = None,
                      clear_strings: str = None,
                      files_to_clear: list = None,
                      files_to_delete: list = None):
        """ Anonymize logfile. The method removes the specified strings as well as the home path from the logfile and
        removes certain json fields (['environment']['platform']['node'] and ['ip']).

        Keyword arguments:
        out_log_name -- output logfile (default is the logfile name appended with _public)
        clear_strings -- strings to be removed
        files_to_clear -- additional files to clear from the specified strings
        files_to_delete -- files to delete
        """
        if CmdInterface.__logfile_name is None or not os.path.isfile(CmdInterface.__logfile_name):
            return

        if clear_strings is None:
            clear_strings = list()
        if files_to_clear is None:
            files_to_clear = list()
        if files_to_delete is None:
            files_to_delete = list()
        clear_strings.append(str(Path.home()))

        print('Anonymizing ' + CmdInterface.__logfile_name)
        if out_log_name is None:
            out_log_name = CmdInterface.__logfile_name.replace('.json', '_public.json')

        try:
            f_in = open(CmdInterface.__logfile_name, 'r')
            file_content = f_in.read()
            for cl in clear_strings:
                file_content = file_content.replace(cl, '')
            f_in.close()
            f_out = open(out_log_name, 'w')
            f_out.write(file_content)
            f_out.close()
        except Exception as err:
            print('Exception: ' + str(err))
            print(err.args)

        try:
            data = list()
            if os.path.isfile(out_log_name):
                with open(out_log_name) as f:
                    data = json.load(f)
            to_remove = list()
            for log in data:
                if log['command']['name'] == 'anonymize_log':
                    to_remove.append(log)
                    continue
                del log['environment']['platform']['node']
                if 'ip' in log['environment']['platform'].keys():
                    del log['environment']['platform']['ip']
            for log in to_remove:
                data.remove(log)
            with open(out_log_name, 'w') as f:
                json.dump(data, f, indent=2, sort_keys=False)
        except Exception as err:
            print('Exception: ' + str(err))
            print(err.args)

        for file in files_to_clear:
            if os.path.isfile(file):
                print('Anonymizing ' + file)
                try:
                    f_in = open(file, 'r')
                    file_content = f_in.read()
                    for cl in clear_strings:
                        file_content = file_content.replace(cl, '')
                    f_in.close()
                    f_out = open(file, 'w')
                    f_out.write(file_content)
                    f_out.close()
                except Exception as err:
                    print('Exception: ' + str(err))
                    print(err.args)

        for file in files_to_delete:
            if os.path.isfile(file):
                print('Removing ' + file)
                try:
                    os.remove(file)
                except Exception as err:
                    print('Exception: ' + str(err))
                    print(err.args)

    def run(self, version_arg: str = None,
            pre_command: str = None,
            check_input: list = None,
            check_output: list = None,
            silent: bool = False) -> int:
        """Run command and save provenance information.

        Keyword arguments:
        version_arg -- the specified command line tool is run with only this argument before running the actual
                       command to print the version info (string)
        pre_command -- this command is run in the same terminal session before the main command (optional, string)
        check_input -- check that all of the specified files are available before running the app
                       (optional, list of strings)
        check_output -- check that at least one of the specified files is missing to avoid unnecessary rerun
                        (optional, list of strings)
        silent -- don't creat log entry for this command

        Return codes: 0=not run, 1=run successful, 2=run not necessary,
                      -1=output missing after run, -2=input missing, -3=exception
        """
        return_code = 0
        if check_input is None:
            check_input = list()
        if check_output is None:
            check_output = list()
        check_input += self.__check_input
        check_output += self.__check_output
        self.__py_function_return = None

        # check if run has been called recoursively (CmdInterface inside of CmdInterface)
        self.__nested = False
        self.__no_new_log = silent
        self.__silent = silent
        if CmdInterface.__called:
            self.__no_new_log = True
            self.__nested = True
        CmdInterface.__called = True

        # check if run is necessary or if output is already present
        run_necessary = False
        if len(check_output) == 0 or len(CmdInterface.check_exist(check_output)) > 0:
            run_necessary = True
        else:
            return_code = 2
            if CmdInterface.__immediate_return_on_run_not_necessary:
                self.__log = CmdLog()
                if not self.__nested:
                    CmdInterface.__called = False
                return return_code

        # check if run is prossible or if input is missing
        run_possible = True
        missing_inputs = CmdInterface.check_exist(check_input)
        self.__log['command']['input']['missing'] = missing_inputs
        if len(missing_inputs) > 0:
            run_possible = False
            return_code = -2

        # create actual command string
        if pre_command is not None:
            run_string = pre_command + os.linesep + self.get_run_string()
        else:
            run_string = self.get_run_string()

        # start logging
        self.__log['command']['is_py_function'] = self.__is_py_function
        if self.__is_py_function:
            self.__log['command']['name'] = str(self.__no_key_options[0].__name__)
        else:
            self.__log['command']['name'] = str(self.__no_key_options[0])
        self.__log['command']['input']['expected'] = check_input
        self.__log['command']['output']['expected'] = check_output
        self.__log['command']['run_string'] = run_string

        start_time = self.__log_start()
        self.append_log()

        exception = None
        if run_necessary and run_possible:
            self.__log['command']['input']['found'] = CmdInterface.get_file_hashes(check_input)

            try:
                # run command
                if self.__is_py_function:
                    self.__pyfunction_to_log()  # command is python function
                else:
                    self.__cmd_to_log(run_string=run_string,
                                      version_arg=version_arg)  # command is external tool

                # check if output was produced as expected
                missing_output = CmdInterface.check_exist(check_output)
                if len(missing_output) > 0:
                    self.log_message('Something went wrong! Expected output files are missing: ' + str(missing_output))
                    self.__log['command']['output']['missing'] = missing_output
                    return_code = -1
                    exception = MissingOutputError(missing_output)
                else:
                    # everything went as expected
                    self.__log['command']['output']['found'] = CmdInterface.get_file_hashes(check_output)
                    return_code = 1
            except MissingOutputError as err:
                return_code = -1
                exception = err

                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                self.log_message('Exception: ' + exc_type.__name__)
                self.log_message('In file: ' + fname)
                self.log_message('Line: ' + str(exc_tb.tb_lineno))
            except MissingInputError as err:
                return_code = -2
                exception = err

                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                self.log_message('Exception: ' + exc_type.__name__)
                self.log_message('In file: ' + fname)
                self.log_message('Line: ' + str(exc_tb.tb_lineno))
            except Exception as err:
                return_code = -3
                exception = err

                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                self.log_message('Exception: ' + exc_type.__name__)
                self.log_message('In file: ' + fname)
                self.log_message('Line: ' + str(exc_tb.tb_lineno))

        elif not run_necessary:
            self.log_message('Skipping execution. All output files already present.')

        elif not run_possible:
            self.log_message('Skipping execution. Input files missing: ' + str(missing_inputs))
            exception = MissingInputError(missing_inputs)

        if not self.__nested:
            CmdInterface.__called = False

        # end logging
        self.__log_end(start_time, return_code=return_code)

        self.__log = CmdLog()
        if (CmdInterface.__throw_on_error or CmdInterface.__exit_on_error) and return_code <= 0:
            if CmdInterface.__throw_on_error or self.__nested:
                if exception is not None:
                    raise exception
                else:
                    raise Exception('Exiting due to error: ' + self.__return_code_meanings[return_code])
            elif CmdInterface.__exit_on_error:
                exit()

        return return_code
