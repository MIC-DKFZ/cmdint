from setuptools import setup

setup(name='cmdint',
      version='3.0.2',
      description='Enables detailed logging of command line calls in a very lightweight manner.',
      long_description='CmdInterface enables detailed logging of command line and python experiments in a very lightweight manner (coding wise). It wraps your command line or python function calls in a few lines of code and logs everything you might need to reproduce the experiment later on or to simply check what you did a couple of years ago.',
      url='https://github.com/MIC-DKFZ/cmdint/',
      author='Peter F. Neher',
      author_email='p.neher@dkfz.de',
      license='Apache 2.0',
      packages=['cmdint'],
      install_requires=[
          'xmltodict',
          'chardet',
          'psutil',
          'python-telegram-bot',
          'slackclient',
          'GitPython'
      ],
      zip_safe=False,
      classifiers=[
          'Programming Language :: Python :: 3',
          'Operating System :: OS Independent',
          'Development Status :: 5 - Production/Stable'
      ], )
