import telegram.ext as tex
import logging
import ffmpeg
import typing
# import io

from mudeer.com.com_types import ComTypes

# from io import BytesIO


class Telegram():
    """
    processes any Message (Text or speach) and forwards it to the Message pipeline.
    Speech is also processed to text, unsing TTS (e.g. DeepSpeech)
    """

    def __init__(self, settings: dict, name: str, stt, process: typing.Callable[[str, dict, ComTypes], typing.Tuple[bool, str]]):
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

        text_handler = tex.MessageHandler(tex.Filters.text, self.get_callback_text)
        self.dispatcher.add_handler(text_handler)

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

        mime_type = update.message.voice.mime_type
        if mime_type != "audio/ogg":
            self.log.fatal("Wronge Mime Type, recived: {}, expected audio/ogg".format(mime_type))
            context.bot.send_message(chat_id=update.effective_chat.id, text="got some error")
            return

        file_size = float(update.message.voice.file_size)
        self.log.debug("file size: {} MB".format(file_size/1024/1024))
        self.log.debug("mime Type: {}".format(mime_type))

        file = update.message.voice.get_file()
        data = file.download_as_bytearray()

        text = self.stt.process_voice_opus({"name": "tbd"}, data)

        _, return_str = self.process(text, context.chat_data, ComTypes.TELEGRAM)

        context.bot.send_message(chat_id=update.effective_chat.id, text=return_str)

    def get_callback_text(self, update, context):
        text = update.message.text
        _, return_str = self.process(text.lower(), context.chat_data, ComTypes.TELEGRAM)
        context.bot.send_message(chat_id=update.effective_chat.id, text=return_str)
