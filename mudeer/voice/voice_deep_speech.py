import deepspeech
import numpy
import scipy.signal
import wave
import logging
import datetime
import os


class VoiceDeepSpeech():
    def __init__(self, model_path, scorer_path, record_wav=False, record_user=[]):
        self.log = logging.getLogger(__name__)

        self.record_wav = record_wav
        self.record_user = record_user
        self.model_sample_rate = 16000

        if self.record_wav:
            for user in self.record_user:
                try:
                    os.mkdir(user)
                except FileExistsError:
                    pass

        self.deepspeech = deepspeech.Model(model_path)

        self.scorer_enabled = False
        if scorer_path:
            self.deepspeech.enableExternalScorer(scorer_path)
            self.scorer_enabled = True

        self.log.debug("Init compleat")

    def add_hot_words(self, hot_words, boost=15.0):
        if self.scorer_enabled:
            for word in hot_words:
                # 15 seems to be recommended: https://discourse.mozilla.org/t/how-can-i-know-what-boost-value-to-give-for-a-particular-hot-word/73869/6
                for w in word.split(" "):  # ensure, that we do only have individual words
                    self.log.debug("Add word \"{}\"".format(w))
                    self.deepspeech.addHotWord(w, boost)

    def remove_hot_words(self, hot_words):
        if self.scorer_enabled:
            for word in hot_words:
                for w in word.split(" "):  # ensure, that we do only have individual words
                    self.log.debug("Remove word \"{}\"".format(w))
                    self.deepspeech.eraseHotWord(w)

    def process_voice(self, user, sound_chunk, sample_rate: int):
        # resample for deepspeech
        self.log.debug("Got Voice from {}".format(user["name"]))

        number_of_samples = round(len(sound_chunk) * float(self.model_sample_rate) / sample_rate)
        sound_chunk = scipy.signal.resample(sound_chunk, number_of_samples)
        sound_chunk = numpy.around(sound_chunk).astype(numpy.int16)

        # sst
        text = self.deepspeech.stt(sound_chunk)
        self.log.debug("Understood ({}): {}".format(user["name"], text))
        # self.com.send_to_my_channel(text)

        self.write_wav(user["name"], sound_chunk, text)
        return text

    def process_voice_raw(self, user, sound_chunk):
        # resample for deepspeech
        self.log.debug("Got Voice from {}".format(user["name"]))

        # sst
        text = self.deepspeech.stt(sound_chunk)
        self.log.debug("Understood ({}): {}".format(user["name"], text))
        # self.com.send_to_my_channel(text)

        self.write_wav(user["name"], sound_chunk, text)
        return text

    def write_wav(self, user_name, data, text):
        if self.record_wav:
            if user_name in self.record_user:
                filename = os.path.join(user_name, datetime.datetime.now().strftime("savewav_%Y-%m-%d_%H-%M-%S_%f.wav"))
                self.log.debug("write wav %s", filename)
                with wave.open(filename, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)  # e.g. 16 bit
                    wf.setframerate(self.model_sample_rate)
                    wf.writeframes(data)
                with open(filename + ".txt", "w") as f:
                    f.write(text)
