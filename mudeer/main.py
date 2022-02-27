import logging
import time
import typing
import importlib
import traceback

import mudeer.voice.voice_deep_speech as voice_deep_speech
import mudeer.com.mumble as mumble
import mudeer.com.telegram as telegram
from mudeer.com.com_types import ComTypes
import mudeer.skills


class MuDeer():
    def __init__(self, config):
        self.log = logging.getLogger(__name__)

        self.name = config["etc"]["name"]

        self.log.debug("Init DeepSpeech")
        self.stt = voice_deep_speech.VoiceDeepSpeech(
            config["deepspeech"]["model"],
            config["deepspeech"]["scorer"],
            config["deepspeech"]["record_wav"].lower() == "true",
            config["deepspeech"]["record_user"].split(","))
        self.stt.add_hot_words([self.name.lower()], 20)

        self.log.debug("Init Mumble")

        self.global_context = {}
        self.coms = {}
        self.skills = mudeer.skills.Skills()

        self.coms["mumble"] = mumble.Mumble(config["mumble"], self.name, self.stt, self.process)
        self.coms["telegram"] = telegram.Telegram(config["telegram"], self.name, self.stt, self.process)

    def connect(self):
        for com in self.coms:
            self.coms[com].connect()

    def disconnect(self):
        for com in self.coms:
            self.coms[com].disconnect()

    def process(self, text: str, chat_context: dict, source: ComTypes) -> typing.Tuple[bool, str]:
        if "!!reload!!" in text:
            self.log.warn("reload initalised by \"{}\"".format(text))
            try:
                mudeer.skills = importlib.reload(mudeer.skills)
                mudeer.skills.reload()
                self.skills = mudeer.skills.Skills()
            except ImportError as e:
                self.log.fatal("reload failed:\n{}".format(traceback.format_exc()))
                return (False, "reload failed:\n{}".format(e))
            self.log.warn("reload successful")
            return (False, "reload successful")
        else:
            try:
                return self.skills.process(text, chat_context, self.global_context, self.coms, source)
            except KeyboardInterrupt:
                raise
            except SystemExit:
                raise
            except Exception as e:
                self.log.fatal("Got Error during Processing:\n{}".format(traceback.format_exc()))
                return (False, "I got some Error")

    def run(self):
        try:
            while True:
                time.sleep(0.01)
        except KeyboardInterrupt:
            self.log.info("got Interupt, cleaning up")
            self.skills.stop()
