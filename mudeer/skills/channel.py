import typing
import logging
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


class Channel(BasicSkill):
    def __init__(self):
        self.log = logging.getLogger(__name__)

    def get_key_words(self) -> typing.List[str]:
        return ["channel", "kanal"]

    def create_channel(self, channel_name: str, coms: dict) -> bool:
        if "mumble" in coms:
            com: mudeer.com.mumble.Mumble = coms["mumble"]
            self.log.debug("old availabe channels {}".format(com.bot.channels))
            com.bot.channels.new_channel(parent_id=0, name=channel_name)
            self.log.debug("new availabe channels {}".format(com.bot.channels))

            return (False, "Kanal \"{}\" erstellt".format(channel_name))
        else:
            return (False, "Mein Mumble Interface ist nicht online!")

    def process(self, text: str, chat_context: dict, global_context: dict, coms: dict) -> typing.Tuple[bool, str]:
        ret = (False, "AHHHHH .... Irgendwas ist schiefgelaufen ... ")

        state = chat_context.get("channel:state", STATE.INIT)
        self.log.debug("loaded state {}".format(state, state is STATE.INIT))

        if state is STATE.INIT:
            state = STATE.WAIT_FOR_NAME
            ret = (True, "Wie soll der neue Kanal heißen?")

        elif state is STATE.WAIT_FOR_NAME:
            state = STATE.INIT
            channel_name = text
            ret = self.create_channel(channel_name, coms)

        chat_context["channel:state"] = state
        return ret

    def gen_help(self) -> typing.List[str]:
        return ["channel - create a new channel"]
