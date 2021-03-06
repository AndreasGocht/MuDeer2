import importlib
from multiprocessing.spawn import import_main_path
import typing
import logging
import traceback

from mudeer.skills.basic_skill import BasicSkill
import mudeer.skills.weisheiten
import mudeer.skills.online
import mudeer.skills.channel

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
    mudeer.skills.channel = importlib.reload(mudeer.skills.channel)
    mudeer.skills.channel.reload()


class Skills():
    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.skill_list = []
        for skill in [mudeer.skills.weisheiten, mudeer.skills.online, mudeer.skills.channel]:
            try:
                self.skill_list.append(skill.init())
            except Exception as e:
                self.log.fatal("Error loading Skill: {}".format(e))
                self.log.fatal("Traceback: {}".format(traceback.format_exc()))
                self.log.fatal("Skill won't be available")

    def stop(self):
        for skill in self.skill_list:
            skill.stop()

    def process(self, text: str, chat_context: dict, global_context: dict, coms: dict, source: ComTypes) -> typing.Tuple[bool, str]:
        """
        @return Tuple: necessary mostly for the keep listening
            * (True, Message) if there are follow up messages
            * (False, Message) if there are no follow up commands
        """
        answer = ""
        follow_up = False

        open_follow_ups = chat_context.get("follow_up", [])
        new_follow_ups = []

        if not open_follow_ups:
            skill: BasicSkill
            for skill in self.skill_list:
                for keyword in skill.get_key_words():
                    if keyword in text.lower():
                        # todo: some security, e.g. add chat_context per skill?
                        (_follow_up, _answer) = skill.process(text, chat_context, global_context, coms)
                        if _follow_up:
                            new_follow_ups.append(skill)
                        answer += _answer
                        answer += "\n"
                        follow_up = follow_up or _follow_up
        else:
            skill: BasicSkill
            for skill in open_follow_ups:
                (_follow_up, _answer) = skill.process(text, chat_context, global_context, coms)
                if _follow_up:
                    new_follow_ups.append(skill)
                answer += _answer
                answer += "\n"
                follow_up = follow_up or _follow_up

        chat_context["follow_up"] = new_follow_ups
        if answer == "":
            return (True, "Das habe ich nicht verstanden")
        else:
            if source == ComTypes.MUMBLE:
                answer = answer.replace("\n", "<br />")
            return (follow_up, answer)
