import unittest
import git
import os
from pathlib import Path
from cmdint import CmdInterface
from cmdint.Utils import *


def nest():
    print('TOPLEVEL NEST')
    runner = CmdInterface(dummy_func)
    runner.run()


def dummy_func():
    print('dummy')


def dummy_exception():
    raise Exception('DUMMY ERROR')


class CmdInterfaceTests(unittest.TestCase):

    def setUp(self):
        CmdInterface.set_throw_on_error(True)
        CmdInterface.set_exit_on_error(False)

    def test1(self):
        with self.assertRaises(OSError):
            CmdInterface('bla')

    def test2(self):
        with self.assertRaises(NotADirectoryError):
            CmdInterface.add_repo_path('bla')

    def test3(self):
        with self.assertRaises(git.exc.InvalidGitRepositoryError):
            CmdInterface.add_repo_path(str(Path.home()))

    def test4(self):
        runner = CmdInterface(dummy_func)
        output = runner.run()
        self.assertEqual(output, 1)
        self.assertTrue(os.path.isfile('CmdInterface.json'))
        os.remove('CmdInterface.json')

    def test5(self):
        with self.assertRaises(OSError):
            runner = CmdInterface('cp')
            runner.run(silent=True)
        self.assertTrue(not os.path.isfile('CmdInterface.json'))

    def test6(self):
        with self.assertRaises(Exception):
            runner = CmdInterface(dummy_exception)
            runner.run(silent=True)
        self.assertTrue(not os.path.isfile('CmdInterface.json'))

    def test7(self):
        CmdInterface.set_static_logfile('CmdInterface.json', delete_existing=True)
        CmdInterface.set_throw_on_error(False)
        CmdInterface.set_exit_on_error(True)
        with self.assertRaises(SystemExit):
            runner = CmdInterface(dummy_exception)
            runner.run(silent=False)
        self.assertTrue(os.path.isfile('CmdInterface.json'))
        os.remove('CmdInterface.json')

    def test8(self):
        with self.assertRaises(MissingInputError):
            runner = CmdInterface('cp')
            runner.add_arg(arg='NotExistingFile.txt', check_input=True)
            runner.add_arg(arg='NotExistingFile.txt')
            runner.run(silent=True)
        self.assertTrue(not os.path.isfile('CmdInterface.json'))

    def test9(self):
        print(__file__)
        with self.assertRaises(MissingOutputError):
            runner = CmdInterface('echo')
            runner.add_arg(arg='TEST', check_output=True)
            runner.run(silent=True)
        self.assertTrue(not os.path.isfile('CmdInterface.json'))

    def test10(self):
        print(__file__)
        CmdInterface.set_static_logfile('/home/neher/cmdint/test/CmdInterface.json', delete_existing=True)
        runner = CmdInterface(nest)
        runner.run(silent=False)
        self.assertTrue(os.path.isfile('/home/neher/cmdint/test/CmdInterface.json'))
        os.remove('CmdInterface.json')

    # TODO: check logfile contents


if __name__ == '__main__':
    unittest.main()
