import requests
import re
import html
import random
import logging
import typing

from mudeer.skills.basic_skill import BasicSkill


def reload():
    pass


def add_br(m):
    return m.group(1) + "\n"


class Weisheit(BasicSkill):
    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.weisheiten = []
        parsing = False

        r = requests.get("https://geistige-steinwueste.de/archiv/")

        for line in r.text.split("\n"):
            if "Liste aller bisher veröffentlichten Weisheiten" in line:
                parsing = True
            if parsing:
                if "<td>" in line:
                    weisheit = line.replace("<td>", "").replace("</td>", "")
                    w = re.sub("([0-9][0-9]/[0-9][0-9])", add_br, weisheit)
                    self.weisheiten.append(html.unescape(w))
        self.log.debug("Got {} weisheiten".format(len(self.weisheiten)))

    def get_key_words(self) -> typing.List[str]:
        return ["weisheit", "weißheit"]

    def process(self, text: str, chat_context: dict, global_context: dict, coms: dict) -> typing.Tuple[bool, str]:
        weisheit = random.choice(self.weisheiten)
        self.log.debug("Sende weisheit \"{}\"".format(weisheit))
        return (False, weisheit)

    def gen_help(self) -> typing.List[str]:
        return ["weisheit - Eine Weisheit von Felix"]
