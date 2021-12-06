import requests
import re
import html
import random
import logging
import os
import json
import datetime
import time


def add_br(m):
    return m.group(1) + "<br/>"


class Weisheit():
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

    def get_key_words(self):
        return ["weisheit"]

    def process(self):
        weisheit = random.choice(self.weisheiten)
        self.log.debug("Sende weisheit \"{}\"".format(weisheit))
        return weisheit

    def gen_help(self):
        return ["weisheit - Eine Weisheit von Felix"]
