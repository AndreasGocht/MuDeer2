import typing
import logging
import threading
import pymumble_py3
from enum import Enum


import mudeer.com.mumble
from mudeer.skills.basic_skill import BasicSkill


def reload():
    pass


# WARNING! Reloading wont affet the enumeration.
# So each comparision after reload will become false!
class STATE(Enum):
    INIT = 0
    WAIT_FOR_NAME = 1
    WAIT_FOR_TIME = 2


def init():
    return Channel()


class Channel(BasicSkill):
    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.timers = []

    def stop(self):
        for timer in self.timers:
            if timer.is_alive():
                timer.cancel()

    def get_key_words(self) -> typing.List[str]:
        return ["channel", "kanal"]

    def run_in(self, time: float, function, args=None, kwargs=None):
        timer = threading.Timer(time, function=function, args=args, kwargs=kwargs)
        self.timers.append(timer)
        timer.start()

    def create_channel(self, channel_name: str, coms: dict) -> bool:
        if "mumble" in coms:
            com: mudeer.com.mumble.Mumble = coms["mumble"]
            self.log.debug("old availabe channels {}".format(com.bot.channels))
            com.bot.channels.new_channel(parent_id=0, name=channel_name)
            self.log.debug("new availabe channels {}".format(com.bot.channels))

            return (False, "Kanal \"{}\" erstellt".format(channel_name))
        else:
            return (False, "Mein Mumble Interface ist nicht online!")

    def try_delete_channel(self, channel_name: str, coms: dict):
        self.log.debug("Trying to delete Channel {}".format(channel_name))
        self.log.debug("Available Coms: {}".format(coms.keys()))
        if "mumble" not in coms:
            self.log.error("Mumble not in Coms. Cannot remove the channel \"{}\"".format(channel_name))
            return

        com: mudeer.com.mumble.Mumble = coms["mumble"]
        try:
            channel = com.bot.channels.find_by_name(channel_name)
        except pymumble_py3.error.UnknownChannelError:
            self.log.error("Can not find Channel \"{}\" in the follofiwng chanels: {}".fomrat(
                channel_name, com.bot.channels))

        users = channel.get_users()
        if len(users) == 0:
            logging.debug("Removing the channel")
            channel.remove()
        else:
            logging.debug("there are still users in the channel. Trying later")
            self.run_in(1*60, self.try_delete_channel, args=[channel_name, coms])

    def process(self, text: str, chat_context: dict, global_context: dict, coms: dict) -> typing.Tuple[bool, str]:
        ret = (False, "AHHHHH .... Irgendwas ist schiefgelaufen ... ")

        state = chat_context.get("channel:state", STATE.INIT)
        self.log.debug("loaded state {}".format(state, state is STATE.INIT))

        if state is STATE.INIT:
            state = STATE.WAIT_FOR_NAME
            ret = (True, "Wie soll der neue Kanal heißen?")

        elif state is STATE.WAIT_FOR_NAME:
            state = STATE.WAIT_FOR_TIME
            chat_context["channel:name"] = text
            ret = (True, "Wie lange soll der Kanal mindestens offen bleiben? (Minuten)")

        elif state is STATE.WAIT_FOR_TIME:
            try:
                minutes = int(text)
                state = STATE.INIT
                channel_name = chat_context["channel:name"]
                ret = self.create_channel(channel_name, coms)
                self.run_in(minutes*60, self.try_delete_channel, args=[channel_name, coms])
            except ValueError:
                ret = (True, "Sorry, das konnte ich nicht in Minuten umwandeln. Bitte versuchs noch mal!")

        chat_context["channel:state"] = state
        return ret

    def gen_help(self) -> typing.List[str]:
        return ["channel - create a new channel"]
