import logging
import typing

import mudeer.com.mumble


def reload():
    pass


class Online():
    def __init__(self):
        self.log = logging.getLogger(__name__)

    def get_key_words(self):
        return ["online"]

    def process(self, chat_context: dict, global_context: dict, coms: dict) -> typing.Tuple[bool, str]:
        if "mumble" in coms:
            com: mudeer.com.mumble.Mumble = coms["mumble"]
        else:
            return (False, "Mein Mumble Interface ist nicht online!")

        answer = "Die folgenden Nutzer sind online:\n"
        for user in com.bot.users.values():
            answer += "* " + user["name"] + "\n"
        return (False, answer)

    def gen_help(self):
        return ["online - Wer ist im Mumble online?"]
