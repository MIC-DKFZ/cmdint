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
        print('Test 1 start')
        with self.assertRaises(OSError):
            CmdInterface('bla')
        print('Test 1 end')

    def test2(self):
        print('Test 2 start')
        with self.assertRaises(NotADirectoryError):
            CmdInterface.add_repo_path('bla')
        print('Test 2 end')

    def test3(self):
        print('Test 3 start')
        with self.assertRaises(git.exc.InvalidGitRepositoryError):
            CmdInterface.add_repo_path(str(Path.home()))
        print('Test 3 end')

    def test4(self):
        print('Test 4 start')
        runner = CmdInterface(dummy_func)
        output = runner.run()
        self.assertEqual(output, 1)
        self.assertTrue(os.path.isfile('CmdInterface.json'))
        os.remove('CmdInterface.json')
        print('Test 4 end')

    def test5(self):
        print('Test 5 start')
        with self.assertRaises(OSError):
            runner = CmdInterface('cp')
            runner.run(silent=True)
        self.assertTrue(not os.path.isfile('CmdInterface.json'))
        print('Test 5 end')

    def test6(self):
        print('Test 6 start')
        with self.assertRaises(Exception):
            runner = CmdInterface(dummy_exception)
            runner.run(silent=True)
        self.assertTrue(not os.path.isfile('CmdInterface.json'))
        print('Test 6 end')

    def test7(self):
        print('Test 7 start')
        CmdInterface.set_static_logfile('CmdInterface.json', delete_existing=True)
        CmdInterface.set_throw_on_error(False)
        CmdInterface.set_exit_on_error(True)
        with self.assertRaises(SystemExit):
            runner = CmdInterface(dummy_exception)
            runner.run(silent=False)
        self.assertTrue(os.path.isfile('CmdInterface.json'))
        os.remove('CmdInterface.json')
        print('Test 7 end')

    def test8(self):
        print('Test 8 start')
        with self.assertRaises(MissingInputError):
            runner = CmdInterface('cp')
            runner.add_arg(arg='NotExistingFile.txt', check_input=True)
            runner.add_arg(arg='NotExistingFile.txt')
            runner.run(silent=True)
        self.assertTrue(not os.path.isfile('CmdInterface.json'))
        print('Test 8 end')

    def test9(self):
        print('Test 9 start')
        with self.assertRaises(MissingOutputError):
            runner = CmdInterface('echo')
            runner.add_arg(arg='TEST', check_output=True)
            runner.run(silent=True)
        self.assertTrue(not os.path.isfile('CmdInterface.json'))
        print('Test 9 end')

    def test10(self):
        print('Test 10 start')
        runner = CmdInterface(nest)
        runner.run(silent=True)
        print('Test 10 end')

    def test11(self):
        print('Test 11 start')
        CmdInterface.set_static_logfile('CmdInterface.json', delete_existing=True, pack_source_files=True)
        runner = CmdInterface(dummy_func)
        output = runner.run()
        self.assertEqual(output, 1)
        self.assertTrue(os.path.isfile('CmdInterface.json'))
        run_log = CmdInterface.load_log('CmdInterface.json')[-1]
        self.assertTrue(os.path.isfile(run_log['source_tarball']))
        # os.remove(run_log['source_tarball'])
        os.remove('CmdInterface.json')
        print('Test 11 end')

    # TODO: check logfile contents


if __name__ == '__main__':
    unittest.main()
