import deepspeech
import numpy
import wave
import logging
import datetime
import os
import io
import scipy
import scipy.signal
import pyogg
import ctypes


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

        # self.opus_decoder = pyogg.opus_decoder.OpusDecoder()
        # self.opus_decoder.set_sampling_frequency(self.model_sample_rate)
        # self.opus_decoder.set_channels(1)

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

    def process_voice(self, user, sound_chunk):
        text = self.deepspeech.stt(sound_chunk)
        self.log.debug("Understood ({}): \"{}\"".format(user["name"], text))
        self.write_wav(user["name"], sound_chunk, text)
        return text

    def process_voice_chunk(self, user, sound_chunk, sample_rate: int):
        # resample for deepspeech
        self.log.debug("VOICE_CHUNK: Got Voice from {}".format(user["name"]))

        number_of_samples = round(len(sound_chunk) * float(self.model_sample_rate) / sample_rate)
        sound_chunk = scipy.signal.resample(sound_chunk, number_of_samples)
        sound_chunk = numpy.around(sound_chunk).astype(numpy.int16)

        # data = librosa.util.buf_to_float(data, 2)
        # data = librosa.resample(data, orig_sr=sample_rate, target_sr=self.model_sample_rate)

        # sound_chunk = io.BytesIO()
        # soundfile.write(sound_chunk, data, samplerate=self.model_sample_rate, format="RAW", subtype='PCM_16')

        # self.log.debug("librosa voice_chunk: {}".format(type(data)))

        # sst
        return self.process_voice(user, sound_chunk)

    def process_voice_opus(self, user, sound_chunk: bytearray):
        # resample for deepspeech
        self.log.debug("VOICE_OPUS: Got Voice from {}".format(user["name"]))

        # sound_chunk = self.opus_decoder.decode(sound_chunk)

        opus_data = pyogg.OpusMemeory(sound_chunk)
        self.log.debug("VOICE_OPUS: channels {}, freq {}, bytes_per_sample {}".format(
            opus_data.channels, opus_data.frequency, opus_data.bytes_per_sample))

        sound_chunk = opus_data.as_array()
        self.log.debug("VOICE_OPUS: numpy {}".format(sound_chunk.shape))
        if (opus_data.channels == 2):
            sound_chunk = (sound_chunk[:, 0] + sound_chunk[:, 1])/2
        sound_chunk = numpy.squeeze(sound_chunk)
        self.log.debug("VOICE_OPUS: numpy2 {}".format(sound_chunk.shape))

        number_of_samples = round(len(sound_chunk) * float(self.model_sample_rate) / 48000)
        sound_chunk = scipy.signal.resample(sound_chunk, number_of_samples)
        sound_chunk = numpy.around(sound_chunk).astype(numpy.int16)

        # data, samplerate = soundfile.read(sound_file, dtype='float32', format=codec)
        # data = librosa.to_mono(data)
        # data = librosa.resample(data, orig_sr=samplerate, target_st=self.model_sample_rate)

        # sound_chunk = io.BytesIO()
        # soundfile.write(sound_chunk, data, samplerate=self.model_sample_rate, format="RAW", subtype='PCM_16')

        # self.log.debug("librosa voice_file: {}".format(type(sound_chunk)))

        # sst
        return self.process_voice(user, sound_chunk)

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
