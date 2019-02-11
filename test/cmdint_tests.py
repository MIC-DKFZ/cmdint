import unittest
import git
import os
from pathlib import Path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../cmdint/')
from cmdint import CmdInterface


def dummy_func():
    print('dummy')


class CmdInterfaceTests(unittest.TestCase):

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

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
