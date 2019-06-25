from slack import WebClient
import telegram
from abc import ABC, abstractmethod


class MessageLogger(ABC):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def send_message(self, message: str):
        pass

    @abstractmethod
    def send_file(self, file: str, message: str = None):
        pass


class SlackMessageLogger(MessageLogger):
    """
    Receive slack messages of your CmdInterface runs. How to get a bot user OAuth access token:
    https://api.slack.com/bot-users
    """

    def __init__(self, token: str, channel_or_user: str, caption: str = None):
        super().__init__()

        self.slack_client = WebClient(token=token)
        self.cid = None
        self.caption = caption
        for el in self.slack_client.api_call("users.list")['members']:
            if el['name'] == channel_or_user:
                self.cid = el['id']
        for el in self.slack_client.api_call("conversations.list")['channels']:
            if el['name'] == channel_or_user:
                self.cid = el['id']

        if self.cid is None:
            raise Exception('Slack channel or user id unknown for specified token')

    def send_message(self, message: str):
        if message is None:
            return

        if self.caption is not None:
            message = self.caption + ":\n" + message
        retval = self.slack_client.api_call(
            "chat.postMessage",
            channel=self.cid,
            text=message
        )
        if not retval['ok']:
            print("Could not send message to slack: " + str(retval))

    def send_file(self, file: str, message: str = None):
        if file is None:
            return

        try:
            if self.caption is not None:
                message = self.caption + ":\n" + message
            retval = self.slack_client.api_call(
                "files.upload",
                channels=self.cid,
                file=open(file),
                initial_comment=message
            )
            if not retval['ok']:
                print("Could not send message to slack: " + str(retval))
        except Exception as err:
            print("Could not send message to slack: " + str(err))


class TelegramMessageLogger(MessageLogger):
    """
    Receive telegram messages of your CmdInterface runs. How to get a token and chat_id:
    https://github.com/python-telegram-bot/python-telegram-bot/wiki/Introduction-to-the-API
    """

    def __init__(self, token: str, chat_id: str, caption: str = None):
        super().__init__()

        self.bot = telegram.Bot(token=token)
        self.cid = chat_id
        self.caption = caption

    def send_message(self, message: str):

        if self.bot is not None:
            try:
                if self.caption is not None:
                    message = self.caption + ":\n" + message
                self.bot.send_message(chat_id=self.cid, text=message)
            except Exception as err:
                print("Could not send message to telegram: " + str(err))

    def send_file(self, file: str, message: str = None):
        if self.bot is not None:
            try:
                text = None
                if self.caption is not None:
                    text = self.caption
                if message is not None:
                    if text is None:
                        text = message
                    else:
                        text += '\n' + message
                self.bot.send_document(chat_id=self.cid,
                                       document=open(file, 'rb'),
                                       caption=text)
            except Exception as err:
                print("Could not send file to telegram: " + str(err))
