import logging
import time

import mudeer.voice.voice_deep_speech as voice_deep_speech


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

    def connect(self):
        self.coms.connect()

    def run(self):
        while True:
            time.sleep(0.01)

    def disconnect(self):
        pass
