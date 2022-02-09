import os
import subprocess
from datetime import datetime
import time
import git
import hashlib
import inspect
import json
import io
import chardet
from pathlib import Path
from shutil import which
from cmdint.Utils import *
from cmdint import MessageLogger
import tarfile
import uuid


class CmdInterface:
    """
    Enables detailed logging of command line calls in a very lightweight manner (coding wise). Also supports logging of
    python functions. CmdInterface logs information regarding the command version, command execution, the input and
    output, execution times, platform and python environment information as well as git repository information.
    """

    # private
    __logfile_name: str = 'CmdInterface.json'
    __pack_source_files: bool = False
    __git_repos: dict = dict()
    __return_code_meanings: dict = {0: 'not run',
                                    1: 'run successful',
                                    2: 'run not necessary',
                                    -1: 'output missing after run',
                                    -2: 'input missing',
                                    -3: 'exception'}
    __autocommit_mainfile_repo: bool = False
    __autocommit_mainfile_repo_done: bool = False
    __immediate_return_on_run_not_necessary: bool = True
    __exit_on_error: bool = False
    __throw_on_error: bool = True
    __use_installer: bool = False
    __installer_replacements: list = list()
    __installer_command_suffix: str = '.sh'
    __print_messages: bool = True
    __cmdint_text_output: list = []
    __called: bool = False  # check for recursion
    __logfile_access_lost: bool = False
    __run_id: str = ''

    # messenger logging
    __message_logger: MessageLogger.MessageLogger = None
    __message_log_level: MessageLogLevel = MessageLogLevel.START_AND_END_MESSAGES

    def __init__(self, command, static_logfile: str = None, description: str = None):
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
        self.__log['description'] = description

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
                            log_level: MessageLogLevel = MessageLogLevel.START_AND_END_MESSAGES):
        """
        Receive telegram messages of your CmdInterface runs. How to get a token and chat_id:
        https://github.com/python-telegram-bot/python-telegram-bot/wiki/Introduction-to-the-API
        Steps:
        1. Search for botfather in the telegram search an start a conversation
        2. Type /newbot and follow the instructions of BotFather
        3. Save your token
        4. Search for your bot in the teegram search and start a conversion. SImply send "hello" or something.
        5. Get the chat id by browsing the adress
           https://api.telegram.org/bot[YOUR-TOKEN-HERE-WITHOUT-BRACKETS]/getUpdates
           The number shown in the field "id" is your chat ID
        """
        CmdInterface.__message_log_level = log_level
        if token is None or chat_id is None:
            CmdInterface.__message_logger = None
        else:
            CmdInterface.__message_logger = MessageLogger.TelegramMessageLogger(token=token, chat_id=chat_id, caption=caption)

    @staticmethod
    def set_slack_logger(bot_oauth_token: str,
                         user_or_channel: str,
                         caption: str = None,
                         log_level: MessageLogLevel = MessageLogLevel.START_AND_END_MESSAGES):
        """
        Receive slack messages of your CmdInterface runs. How to get a bot user OAuth access token:
        https://api.slack.com/bot-users
        """
        CmdInterface.__message_log_level = log_level
        if bot_oauth_token is None or user_or_channel is None:
            CmdInterface.__message_logger = None
        else:
            CmdInterface.__message_logger = MessageLogger.SlackMessageLogger(bot_oauth_token, user_or_channel, caption)

    @staticmethod
    def send_message(message: str):
        """
        Send message to the specified service (currently slack or telegram is possible)
        """
        if CmdInterface.__message_logger is not None:
            CmdInterface.__message_logger.send_message(message)

    @staticmethod
    def send_logfile(message: str = None):
        """
        Send logfile to the specified service (currently slack or telegram is possible)
        """
        if CmdInterface.__message_logger is not None and os.path.isfile(CmdInterface.__logfile_name):
            CmdInterface.__message_logger.send_file(file=CmdInterface.get_static_logfile(), message=message)

    @staticmethod
    def get_static_logfile() -> str:
        """
        Return current logfile path.
        """
        return CmdInterface.__logfile_name

    @staticmethod
    def set_static_logfile(file: str, delete_existing: bool = False, pack_source_files: bool = False):
        """
        Set logfile path. Logfiles are stored in json format. Existing logfiles are appended if not specified otherwise.
        If the file does not exist, a new one is created automatically.
        Each toplevel entry of a logfile corresponds to one execution of CmdInterface.run

        If pack_source_files is True, CmdInterface creates a tarball containing the touched python scripts excluding
        the files in "site-packages".
        """
        if CmdInterface.__called:
            print('Nested CmdInterface usage. Logfile not set.')
            return
        CmdInterface.__logfile_name = file
        CmdInterface.__pack_source_files = False
        CmdInterface.__cmdint_text_output = []
        if file is None:
            return
        CmdInterface.__pack_source_files = pack_source_files

        run_logs = CmdInterface.load_log()
        if run_logs is not None and len(run_logs) > 0:
            for run in run_logs:
                if delete_existing and 'source_tarball' in run.keys() and os.path.isfile(str(run['source_tarball'])):
                    os.remove(run['source_tarball'])

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

        # Add git repository of cmdint (if available)
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
        ['time']['start']
        ['time']['utc_offset']
        Return start time.
        """
        if len(CmdInterface.__run_id) == 0:
            CmdInterface.__run_id = str(uuid.uuid4())

        tar = None
        packed_files = []
        if CmdInterface.__pack_source_files:
            tar = tarfile.open(CmdInterface.__logfile_name.replace('.json', '_' + CmdInterface.__run_id + '.tar'), "a")
            packed_files = tar.getnames()
            for i in range(len(packed_files)):
                packed_files[i] = '/' + packed_files[i]

        self.__log['call_stack'] = list()
        for frame in inspect.stack()[1:]:
            el = dict()
            el['file'] = os.path.abspath(str(frame[1]))
            el['line'] = str(frame[2])
            el['function'] = str(frame[3])
            self.__log['call_stack'].append(el)

            if tar is not None and not el['file'].__contains__('site-packages') and el['file'] not in packed_files:
                packed_files.append(el['file'])
                file_name = os.path.basename(el['file'])
                if file_name != 'CmdInterface.py':
                    tar.add(name=el['file'], arcname=el['file'])

        if tar is not None:
            tar.close()

        start_time = datetime.now()
        self.__log['time']['start'] = start_time.strftime("%Y-%m-%d %H:%M:%S")
        self.__log['time']['utc_offset'] = time.localtime().tm_gmtoff
        CmdInterface.log_message(self.__log['name'] + ' START')
        if CmdInterface.__message_log_level == MessageLogLevel.START_AND_END_MESSAGES and not self.__silent:
            CmdInterface.send_message('START ' + self.__log['name'])
        return start_time

    def __log_end(self, start_time: datetime, return_code: int) -> datetime:
        """
        Log end time and duration of command execution:
        ['time']['end']
        ['time']['duration']
        Return end time.
        """

        # set times
        end_time = datetime.now()
        self.__log['time']['end'] = end_time.strftime("%Y-%m-%d %H:%M:%S")

        if start_time is None:
            return
        duration = end_time - start_time
        hours, remainder = divmod(duration.seconds, 3600)
        hours += duration.days * 24
        minutes, seconds = divmod(remainder, 60)
        duration_formatted = '%d:%02d:%02d' % (hours, minutes, seconds)
        self.__log['time']['duration'] = duration_formatted

        # log end messages & return code
        CmdInterface.log_message(self.__log['name'] + ' END')
        if (CmdInterface.__throw_on_error or CmdInterface.__exit_on_error) and return_code <= 0:
            CmdInterface.log_message('Exiting due to error: ' + self.__return_code_meanings[return_code])
        self.__log['return_code'] = return_code
        self.update_log()

        if not self.__silent and \
                CmdInterface.__message_log_level > MessageLogLevel.ONLY_ERRORS or \
                (CmdInterface.__message_log_level == MessageLogLevel.ONLY_ERRORS and return_code <= 0):
            if os.path.isfile(CmdInterface.__logfile_name):
                CmdInterface.send_logfile(
                    message='END ' + self.__log['name'] + '\n' + self.__return_code_meanings[return_code])
            else:
                CmdInterface.send_message(
                    message='END ' + self.__log['name'] + '\n' + self.__return_code_meanings[return_code])

        return end_time

    @staticmethod
    def log_message(message: str, via_messenger: bool = False, add_time: bool = True):
        """
        Store string in log (['cmdint']['output']).
        """
        log_time = ''
        if add_time:
            log_time = datetime.now()
            log_time = log_time.strftime("%Y-%m-%d %H:%M:%S")

        message = str(message)
        if CmdInterface.__print_messages:
            if add_time:
                print(log_time + ' >> ' + message)
            else:
                print(message)

        if add_time:
            CmdInterface.__cmdint_text_output.append([log_time] + message.splitlines())
        else:
            CmdInterface.__cmdint_text_output.append(message.splitlines())
        if via_messenger:
            CmdInterface.send_message(message)

    def __pyfunction_to_log(self):
        """
        Run python function and store terminal output in log (['text_output']).
        """
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = sys.stderr = out_string = io.StringIO()

        exception = None
        try:
            if self.__nested or self.__silent:
                self.__py_function_return = self.__no_key_options[0](*self.__no_key_options[1:], **self.__options)
            else:
                proc = ThreadWithReturn(target=self.__no_key_options[0],
                                        args=self.__no_key_options[1:],
                                        kwargs=self.__options)
                proc.start()
                while proc.is_alive():
                    text_output = list()
                    for line in out_string.getvalue().split('\n'):
                        text_output.append(line.split('\r')[-1])

                    self.__log['text_output'] = text_output
                    self.update_log()
                    time.sleep(5)
                self.__py_function_return, exception = proc.get_retval()

        except Exception as err:
            exception = err
        sys.stdout = original_stdout
        sys.stderr = original_stderr

        if not self.__silent:
            if self.__nested:
                print(out_string.getvalue(), end='')
            else:
                self.__log['text_output'] = out_string.getvalue().split('\n')
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
            self.__log['text_output'].append('')
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
                        self.__log['text_output'].append('')
                    else:
                        self.__log['text_output'][-1] += c
                        if (datetime.now() - start_time).seconds > 5:
                            start_time = datetime.now()
                            self.update_log()
            res_out = proc.stdout.read()
            encoding = chardet.detect(res_out)['encoding']
            if encoding is not None:
                res_out = str(res_out.decode(encoding))
                if self.__nested:
                    print(res_out, end='')
                else:
                    if res_out[:2] != os.linesep:
                        temp = res_out.splitlines()
                        self.__log['text_output'][-1] += temp[0]
                        if len(temp) > 1:
                            self.__log['text_output'] += temp[1:]
                    else:
                        self.__log['text_output'] += res_out.splitlines()
                    self.update_log()

        self.__log['text_output'].append('')
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
                    self.__log['text_output'].append('')
                else:
                    self.__log['text_output'][-1] += c
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
                self.__log['text_output'][-1] += temp[0]
                if len(temp) > 1:
                    self.__log['text_output'] += temp[1:]
            else:
                self.__log['text_output'] += res_out.splitlines()
            self.update_log()

        if proc.returncode != 0 and not self.__ignore_cmd_retval:
            raise OSError(proc.returncode, 'Command line subprocess return value is ' + str(proc.returncode))

    def get_runlogs(self) -> list:
        """
        Load list of run logs and append new run id if necessary.
        """

        if CmdInterface.__logfile_name is None or self.__no_new_log:
            return None

        if len(CmdInterface.__run_id) == 0:
            CmdInterface.__run_id = str(uuid.uuid4())

        run_logs = []
        if os.path.isfile(CmdInterface.__logfile_name):
            with open(CmdInterface.__logfile_name) as f:
                run_logs = json.load(f)

        if len(run_logs) == 0 or run_logs[-1]['run_id'] != CmdInterface.__run_id:
            run_logs.append(RunLog(run_id=CmdInterface.__run_id))

        return run_logs

    def update_log(self):
        """
        Replace last entry of the command log list in the current run log and write to json.
        """
        run_logs = self.get_runlogs()
        if run_logs is None:
            return

        run_logs[-1]['tracked_repositories'] = CmdInterface.__git_repos
        if CmdInterface.__pack_source_files:
            run_logs[-1]['source_tarball'] = CmdInterface.__logfile_name.replace('.json', '_' + CmdInterface.__run_id + '.tar')
        run_logs[-1]['cmdint']['output'] += CmdInterface.__cmdint_text_output

        self.__log['return_code_meaning'] = self.__return_code_meanings[self.__log['return_code']]
        self.__log['options']['no_key'] = CmdInterface.__jsonable(self.__no_key_options[1:])
        self.__log['options']['key_val'] = CmdInterface.__jsonable(self.__options)

        try:
            if len(run_logs[-1]['commands']) == 0:
                run_logs[-1]['commands'].append(self.__log)
            else:
                run_logs[-1]['commands'][-1] = self.__log
            with open(CmdInterface.__logfile_name, 'w') as f:
                json.dump(run_logs, f, indent=2, sort_keys=False)
            CmdInterface.__cmdint_text_output = []
            if CmdInterface.__logfile_access_lost:
                lm = CmdInterface.__print_messages
                CmdInterface.__print_messages = False
                CmdInterface.log_message('Logfile access regained: ' + CmdInterface.__logfile_name, True)
                CmdInterface.__print_messages = lm
            CmdInterface.__logfile_access_lost = False
        except Exception as err:
            if not CmdInterface.__logfile_access_lost:
                error_string = 'Error accessing logfile: ' + CmdInterface.__logfile_name
                error_string += '\n\nException: ' + str(err)
                error_string += '\n\nArgs: ' + str(err.args)
                error_string += '\nProceeding ...'
                lm = CmdInterface.__print_messages
                CmdInterface.__print_messages = False
                CmdInterface.log_message(error_string, True)
                CmdInterface.__print_messages = lm
            CmdInterface.__logfile_access_lost = True

    def append_log(self):
        """
        Append command log to the list held in the run log and write to file. Creates new json if it does not exist.
        """
        run_logs = self.get_runlogs()
        if run_logs is None:
            return

        run_logs[-1]['tracked_repositories'] = CmdInterface.__git_repos
        if CmdInterface.__pack_source_files:
            run_logs[-1]['source_tarball'] = CmdInterface.__logfile_name.replace('.json', '_' + CmdInterface.__run_id + '.tar')
        run_logs[-1]['cmdint']['output'] += CmdInterface.__cmdint_text_output

        self.__log['return_code_meaning'] = self.__return_code_meanings[self.__log['return_code']]
        self.__log['options']['no_key'] = CmdInterface.__jsonable(self.__no_key_options[1:])
        self.__log['options']['key_val'] = CmdInterface.__jsonable(self.__options)

        try:
            run_logs[-1]['commands'].append(self.__log)
            with open(CmdInterface.__logfile_name, 'w') as f:
                json.dump(run_logs, f, indent=2, sort_keys=False)
            CmdInterface.__cmdint_text_output = []
            if CmdInterface.__logfile_access_lost:
                lm = CmdInterface.__print_messages
                CmdInterface.__print_messages = False
                CmdInterface.log_message('Logfile access regained: ' + CmdInterface.__logfile_name, True)
                CmdInterface.__print_messages = lm
            CmdInterface.__logfile_access_lost = False
        except Exception as err:
            if not CmdInterface.__logfile_access_lost:
                error_string = 'Error accessing logfile: ' + CmdInterface.__logfile_name
                error_string += '\n\nException: ' + str(err)
                error_string += '\n\nArgs: ' + str(err.args)
                error_string += '\nProceeding ...'
                lm = CmdInterface.__print_messages
                CmdInterface.__print_messages = False
                CmdInterface.log_message(error_string, True)
                CmdInterface.__print_messages = lm
            CmdInterface.__logfile_access_lost = True

    @staticmethod
    def load_log(logfile_name: str = None) -> list:
        """
        Load the current or the specified json logfile and return as list of dicts.
        """
        if logfile_name is None or not os.path.isfile(logfile_name):
            if CmdInterface.__logfile_name is not None and os.path.isfile(CmdInterface.__logfile_name):
                logfile_name = CmdInterface.__logfile_name
            else:
                return None

        log = list()

        try:
            if os.path.isfile(logfile_name):
                with open(logfile_name) as f:
                    log = json.load(f)
        except Exception as err:
            print('Exception: ' + str(err))
            print(err.args)

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

        if out_log_name is None:
            out_log_name = CmdInterface.__logfile_name.replace('.json', '_public.json')
        print('Anonymizing ' + CmdInterface.__logfile_name + ' --> ' + out_log_name)

        try:
            with open(CmdInterface.__logfile_name, 'r') as f:
                file_content = f.read()
                for cl in clear_strings:
                    file_content = file_content.replace(cl, '')

            with open(out_log_name, 'w') as f:
                f.write(file_content)
        except Exception as err:
            print('Exception: ' + str(err))
            print(err.args)

        try:
            data = list()
            if os.path.isfile(out_log_name):
                with open(out_log_name) as f:
                    data = json.load(f)
            to_remove = list()
            for run_log in data:
                # remove the "anonymize_log" command log in all run logs
                for cmd_log in run_log['commands']:
                    if cmd_log['name'] == 'anonymize_log':
                        to_remove.append(cmd_log)
                        continue
                for cmd_log in to_remove:
                    run_log['commands'].remove(cmd_log)
                # remove personal environment data
                del run_log['environment']['platform']['node']
                if 'ip' in run_log['environment']['platform'].keys():
                    del run_log['environment']['platform']['ip']
            with open(out_log_name, 'w') as f:
                json.dump(data, f, indent=2, sort_keys=False)
        except Exception as err:
            print('Exception: ' + str(err))
            print(err.args)

        for file in files_to_clear:
            if os.path.isfile(file):
                print('Anonymizing ' + file)
                try:
                    with open(file, 'r') as f:
                        file_content = f.read()
                        for cl in clear_strings:
                            file_content = file_content.replace(cl, '')

                    with open(file, 'w') as f:
                        f.write(file_content)

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

        # check if run has been called recursively (CmdInterface inside of CmdInterface)
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
        self.__log['input']['missing'] = missing_inputs
        if len(missing_inputs) > 0:
            run_possible = False
            return_code = -2

        # create actual command string
        if pre_command is not None:
            run_string = pre_command + os.linesep + self.get_run_string()
        else:
            run_string = self.get_run_string()

        # start logging
        self.__log['is_py_function'] = self.__is_py_function
        if self.__is_py_function:
            self.__log['name'] = str(self.__no_key_options[0].__name__)
        else:
            self.__log['name'] = str(self.__no_key_options[0])
        self.__log['input']['expected'] = check_input
        self.__log['output']['expected'] = check_output
        self.__log['run_string'] = run_string

        start_time = self.__log_start()
        self.append_log()

        exception = None
        if run_necessary and run_possible:
            self.__log['input']['found'] = CmdInterface.get_file_hashes(check_input)

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
                    CmdInterface.log_message('Something went wrong! Expected output files are missing: ' + str(missing_output))
                    self.__log['output']['missing'] = missing_output
                    return_code = -1
                    exception = MissingOutputError(missing_output)
                else:
                    # everything went as expected
                    self.__log['output']['found'] = CmdInterface.get_file_hashes(check_output)
                    return_code = 1
            except MissingOutputError as err:
                return_code = -1
                exception = err

                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                error_string = 'Exception type: ' + exc_type.__name__
                error_string += '\n\nException message: ' + str(err)
                error_string += '\n\nIn file: ' + fname
                error_string += '\nLine: ' + str(exc_tb.tb_lineno)
                CmdInterface.log_message(error_string)
            except MissingInputError as err:
                return_code = -2
                exception = err

                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                error_string = 'Exception type: ' + exc_type.__name__
                error_string += '\n\nException message: ' + str(err)
                error_string += '\n\nIn file: ' + fname
                error_string += '\nLine: ' + str(exc_tb.tb_lineno)
                CmdInterface.log_message(error_string)
            except Exception as err:
                return_code = -3
                exception = err

                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                error_string = 'Exception type: ' + exc_type.__name__
                error_string += '\n\nException message: ' + str(err)
                error_string += '\n\nIn file: ' + fname
                error_string += '\nLine: ' + str(exc_tb.tb_lineno)
                CmdInterface.log_message(error_string)

        elif not run_necessary:
            CmdInterface.log_message('Skipping execution. All output files already present.')

        elif not run_possible:
            CmdInterface.log_message('Skipping execution. Input files missing: ' + str(missing_inputs))
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
