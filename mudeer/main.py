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
        self.mumble = mumble.Mumble(config["mumble"], self.name, self.stt, process.process)
        self.telegram = telegram.Telegram(config["telegram"], self.name, self.stt, process.process)

    def connect(self):
        self.mumble.connect()
        self.telegram.connect()

    def disconnect(self):
        self.mumble.disconnect()
        self.telegram.disconnect()

    def run(self):
        while True:
            time.sleep(0.01)
