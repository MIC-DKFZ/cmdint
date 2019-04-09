from cmdint import CmdInterface

'''This example shows how to setup the telegram logging service. You will receive a telegram message each time a 
command execution with CmdInterface started or finished, including the logfile after the command has finished. 
'''

# How to get a telegram bot token and chat_id: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Introduction-to-the-API
# Steps:
# 1. Search for botfather in the telegram search an start a conversation
# 2. Type /newbot and follow the instructions of BotFather
# 3. Save your token
# 4. Search for your bot in the teegram search and start a conversion. SImply send "hello" or something.
# 5. Get the chat id by browsing the adress
#    https://api.telegram.org/bot[YOUR-TOKEN-HERE-WITHOUT-BRACKETS]/getUpdates
#    The number shown in the field "id" is your chat ID
CmdInterface.set_telegram_logger(token='my-telegram-bot-token', chat_id='my-chat-with-bot', caption='TEST')

# create instance of CmdInterface with the name of the command to be called (here "ls")
test = CmdInterface('ls')

# add keyword based argument
test.add_arg(key='-l', arg='/')

# run command
test.run()
