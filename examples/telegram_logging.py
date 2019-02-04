from cmdint import CmdInterface
from pathlib import Path

'''This example shows how to setup the telegram logging service. You will receive a telegram message each time a 
command execution with CmdInterface started or finished, including the logfile after the command has finished. 
'''

# How to get a telegram bot token and chat_id: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Introduction-to-the-API
CmdInterface.set_telegram_logger(token='my-telegram-bot-token', chat_id='my-chat-with-bot', caption='TEST')

# create instance of CmdInterface with the name of the command to be called (here "ls")
test = CmdInterface('ls')

# add keyword based argument
test.add_arg(key='-l', arg=str(Path.home()) + '/cmdint/cmdint/')

# run command
test.run()
