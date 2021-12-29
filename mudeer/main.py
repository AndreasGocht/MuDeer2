import logging
import time

import mudeer.voice.voice_deep_speech as voice_deep_speech
import mudeer.com.mumble as mumble
import mudeer.com.telegram as telegram

import mudeer.process as process


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

        self.coms["mumble"] = mumble.Mumble(config["mumble"], self.name, self.stt, self.process)
        self.coms["telegram"] = telegram.Telegram(config["telegram"], self.name, self.stt, self.process)

    def connect(self):
        for com in self.coms:
            self.coms[com].connect()

    def disconnect(self):
        for com in self.coms:
            self.coms[com].disconnect()

    def process(self, text: str, chat_context: dict) -> str:
        return process.process(text, chat_context, self.global_context, self.coms)

    def run(self):
        while True:
            time.sleep(0.01)
