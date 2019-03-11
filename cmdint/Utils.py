import threading
import socket
import platform
import sys
import math
import multiprocessing
import cmdint
from psutil import virtual_memory
try:
    from pip._internal.operations import freeze
except ImportError:  # pip < 10.0
    from pip.operations import freeze


class CmdLog(dict):
    """
    Log dictionary used to store all logging information captured in CmdInterface.
    """

    def __init__(self):
        super().__init__()
        self['cmd_interface'] = dict()
        self['cmd_interface']['version'] = cmdint.__version__
        self['cmd_interface']['copyright'] = cmdint.__copyright__
        self['cmd_interface']['url'] = 'https://github.com/MIC-DKFZ/cmdint/'
        self['cmd_interface']['output'] = list()
        self['cmd_interface']['repositories'] = None

        self['command'] = dict()
        self['command']['name'] = None
        self['command']['is_py_function'] = False
        self['command']['run_string'] = None
        self['command']['return_code'] = 0
        self['command']['return_code_meaning'] = None
        self['command']['call_stack'] = None
        self['command']['text_output'] = list()
        self['command']['options'] = dict()
        self['command']['options']['no_key'] = None
        self['command']['options']['key_val'] = None

        self['command']['time'] = dict()
        self['command']['time']['start'] = None
        self['command']['time']['end'] = None
        self['command']['time']['duration'] = None
        self['command']['time']['utc_offset'] = None

        self['command']['input'] = dict()
        self['command']['input']['expected'] = list()
        self['command']['input']['found'] = list()
        self['command']['input']['missing'] = list()

        self['command']['output'] = dict()
        self['command']['output']['expected'] = list()
        self['command']['output']['found'] = list()
        self['command']['output']['missing'] = list()

        self['environment'] = dict()
        self['environment']['platform'] = dict()
        self['environment']['platform']['system'] = platform.uname().system
        self['environment']['platform']['release'] = platform.uname().release
        self['environment']['platform']['version'] = platform.uname().version
        self['environment']['platform']['machine'] = platform.uname().machine
        self['environment']['platform']['logical_cores'] = multiprocessing.cpu_count()
        self['environment']['platform']['memory_gb'] = virtual_memory().total / (1024**3)
        self['environment']['platform']['node'] = platform.uname().node
        self['environment']['platform']['ip'] = CmdLog.get_local_ip()
        self['environment']['python'] = dict()
        self['environment']['python']['version'] = platform.python_version()
        self['environment']['python']['build'] = platform.python_build()
        self['environment']['python']['compiler'] = platform.python_compiler()
        self['environment']['python']['implementation'] = platform.python_implementation()
        self['environment']['python']['imported_modules'] = dict()
        for el in sys.modules.keys():
            module = sys.modules[el]
            if hasattr(module, '__version__') and not str(module.__name__).__contains__('.'):
                self['environment']['python']['imported_modules'][str(module.__name__)] = str(module.__version__)

        self['environment']['python']['pip_freeze'] = dict()
        for module in freeze.freeze():
            module = module.split('==')
            if len(module) > 1:
                self['environment']['python']['pip_freeze'][module[0]] = module[1]

    @staticmethod
    def get_local_ip():
        try:
            return [l for l in (
            [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [
                [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in
                 [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]
        except:
            return None


class ProgressBar:
    """
    Helper class to print a simple progress bar to stdout.
    """

    def __init__(self, max):
        self.range = 50
        self.max = max
        self.incr = 1
        if self.max < self.range:
            self.incr = math.ceil(self.range/self.max)
            self.max *= self.incr

        self.c = 0
        self.last_tick = 0
        major = self.range // 10

        for i in range(self.range + 1):
            if i % major == 0:
                pc = str(2 * i) + '%'
                print(pc + ' ' * (self.range // 10 - len(pc)), end='')
        print('')
        for i in range(self.range + 1):
            if i % major == 0:
                print('|', end='')
            else:
                print('-', end='')
        print('')

    def next(self):

        for i in range(self.incr):
            self.c += 1

            if (self.range * self.c) // self.max > self.last_tick:
                self.last_tick = (self.range * self.c) // self.max
                print('*', end='')
            if self.c == self.max:
                print('*')
            sys.stdout.flush()


class MissingInputError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class MissingOutputError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class ThreadWithReturn(threading.Thread):
    """
    Helper class to run python functions in a separate thread and return it's output.
    """

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):
        threading.Thread.__init__(self, group=group, target=target, name=name, args=args, kwargs=kwargs)
        self._return = None
        self._exception = None

    def run(self):
        if self._target is not None:
            try:
                self._return = self._target(*self._args, **self._kwargs)
            except Exception as err:
                self._exception = err

    def get_retval(self):
        threading.Thread.join(self)
        return self._return, self._exception
