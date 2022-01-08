import logging
import typing

import mudeer.com.mumble

from mudeer.skills.basic_skill import BasicSkill


def reload():
    pass


class Online(BasicSkill):
    def __init__(self):
        self.log = logging.getLogger(__name__)

    def get_key_words(self) -> typing.List[str]:
        return ["online"]

    def process(self, text: str, chat_context: dict, global_context: dict, coms: dict) -> typing.Tuple[bool, str]:
        if "mumble" in coms:
            com: mudeer.com.mumble.Mumble = coms["mumble"]
        else:
            return (False, "Mein Mumble Interface ist nicht online!")

        answer = "Die folgenden Nutzer sind online:\n"
        for user in com.bot.users.values():
            answer += "* " + user["name"] + "\n"
        return (False, answer)

    def gen_help(self) -> typing.List[str]:
        return ["online - Wer ist im Mumble online?"]
