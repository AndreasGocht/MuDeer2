import logging
import threading
import numpy
import wave
import ffmpeg
from typing import Callable

from io import BytesIO
import telegram.ext as tex


class Telegram():
    """
    processes any Message (Text or speach) and forwards it to the Message pipeline.
    Speech is also processed to text, unsing TTS (e.g. DeepSpeech)
    """

    def __init__(self, settings: dict, name: str, stt, process: Callable[[str, dict], str]):
        super().__init__()
        self.log = logging.getLogger(__name__)
        self.log.debug("init")

        tex_log = logging.getLogger("telegram.bot")
        tex_log.setLevel(logging.INFO)
        tex_log = logging.getLogger("telegram.ext.dispatcher")
        tex_log.setLevel(logging.INFO)

        # name
        self.user_name = name

        # stt
        self.stt = stt

        self.log.debug("login with token {}".format(settings.get("token", "")))
        self.updater = tex.Updater(token=settings.get("token", ""), use_context=True)
        self.dispatcher = self.updater.dispatcher

        start_handler = tex.CommandHandler("start", self.get_callback_start)
        self.dispatcher.add_handler(start_handler)

        stt_handler = tex.MessageHandler(tex.Filters.voice, self.get_callback_stt)
        self.dispatcher.add_handler(stt_handler)

        self.context = {}
        self.process = process

    def connect(self):
        self.updater.start_polling()

    def disconnect(self):
        self.updater.stop()

    def get_callback_start(self, update, context):
        self.log.debug("got event {}".format(update))
        context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

    def get_callback_stt(self, update, context):
        def normalize_audio(audio):
            out, err = (
                ffmpeg.input("pipe:0", format='ogg')
                .output(
                    "pipe:1",
                    f="WAV",
                    acodec="pcm_s16le",
                    ac=1,
                    ar="16k",
                    loglevel="error",
                    hide_banner=None,
                )
                .run(input=audio, capture_stdout=True, capture_stderr=True)
            )
            if err:
                raise Exception(err)
            return out

        mime = update.message.voice.mime_type
        file_size = float(update.message.voice.file_size)
        self.log.debug("file size: {} MB".format(file_size/1024/1024))

        file = update.message.voice.get_file()
        data = file.download_as_bytearray()

        audio = normalize_audio(data)
        audio = BytesIO(audio)
        with wave.Wave_read(audio) as wav:
            audio = numpy.frombuffer(wav.readframes(wav.getnframes()), numpy.int16)
        text = self.stt.process_voice_raw({"name": "tbd"}, audio)

        return_str = self.process(text, context.chat_data)

        context.bot.send_message(chat_id=update.effective_chat.id, text=return_str)
