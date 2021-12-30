import importlib
import typing
import importlib

import mudeer.skills.weisheiten
import mudeer.skills.online

from mudeer.com.com_types import ComTypes


def reload():
    """
    reload funcitons needs to be static in all modules.
    Initialisation is done together with the Skills Module.
    """
    mudeer.skills.weisheiten = importlib.reload(mudeer.skills.weisheiten)
    mudeer.skills.weisheiten.reload()
    mudeer.skills.online = importlib.reload(mudeer.skills.online)
    mudeer.skills.online.reload()


class Skills():
    def __init__(self):
        self.skill_list = []
        self.skill_list.append(mudeer.skills.weisheiten.Weisheit())
        self.skill_list.append(mudeer.skills.online.Online())

    def process(self, text: str, chat_context: dict, global_context: dict, coms: dict, source: ComTypes) -> typing.Tuple[bool, str]:
        """
        @return Tuple: necessary mostly for the keep listening
            * (True, Message) if there are follow up messages
            * (False, Message) if there are no follow up commands
        """
        answer = ""
        follow_up = False

        for skill in self.skill_list:
            for keyword in skill.get_key_words():
                if keyword in text:
                    # todo: some security, e.g. add chat_context per skill?
                    (_follow_up, _answer) = skill.process(chat_context, global_context, coms)
                    answer += _answer
                    answer += "\n"
                    follow_up = follow_up or _follow_up

        if answer == "":
            return (True, "Das habe ich nicht verstanden")
        else:
            if source == ComTypes.MUMBLE:
                answer = answer.replace("\n", "<br />")
            return (follow_up, answer)
