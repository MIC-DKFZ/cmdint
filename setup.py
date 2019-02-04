from setuptools import setup

setup(name='cmdint',
      version='1.0',
      description='Enables detailed logging of command line calls in a very lightweight manner.',
      long_description='Enables detailed logging of command line calls in a very lightweight manner (coding wise). Also supports logging of python functions. CmdInterface logs information regarding the command version, command execution, the input and output, execution times, platform and python environment information as well as git repository information.',
      url='https://phabricator.mitk.org/source/cmdint/',
      author='Peter F. Neher',
      author_email='p.neher@dkfz.de',
      license='Apache 2.0',
      packages=['cmdint'],
      install_requires=[
          'python-telegram-bot',
          'GitPython'
      ],
      zip_safe=False,
      classifiers=[
          'Programming Language :: Python :: 3.X',
          'Operating System :: Unix',
          'Operating System :: Windows',
          'Operating System :: MacOS'
      ], )