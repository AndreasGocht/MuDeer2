import pymumble_py3 as pymumble
import time
import logging
import numpy
import threading
from typing import Callable

from pymumble_py3 import mumble_pb2


class Mumble(threading.Thread):
    def __init__(self, settings: dict, name: str, stt, process: Callable[[str, dict], str]):
        super().__init__()
        self.log = logging.getLogger(__name__)

        # name
        self.user_name = name
        self.login_name = self.user_name + "Bot"
        self.tag = "@" + self.user_name

        # stt
        self.stt = stt
        self.speech_return_delay = settings.getfloat("speech_return_delay", 0.1)  # when the speech is forwarded

        try:
            self.follow = settings["follow"]
        except KeyError as e:
            raise Exception("Currently the Bot needs to foollow someone!") from e

        # settings
        self.host = settings.get("host", "")
        self.port = settings.getint("port", 64738)
        self.home = settings.get("home_channel", "Bot Home")
        self.pymumble_loop_rate = settings.getfloat("pymumble_loop_rate", 0.05)
        self.cert_file = settings.get("cert_file", None)
        self.key_file = settings.get("key_file", None)
        self.log.debug("self.cert_file: {}".format(self.cert_file))
        self.log.debug("self.key_file: {}".format(self.key_file))

        self.connected = False

        # set up
        self.log.debug("log into mumule server {}:{} with name {}".format(self.host, self.port, self.login_name))
        self.bot = pymumble.Mumble(self.host, self.user_name, port=self.port,
                                   certfile=self.cert_file, keyfile=self.key_file, debug=False)
        self.bot.set_receive_sound(1)
        self.bot.callbacks.set_callback(pymumble.constants.PYMUMBLE_CLBK_TEXTMESSAGERECEIVED,
                                        self.get_callback_text)
        self.bot.callbacks.set_callback(pymumble.constants.PYMUMBLE_CLBK_USERUPDATED,
                                        self.get_callback_user)
        self.bot.callbacks.set_callback(pymumble.constants.PYMUMBLE_CLBK_USERCREATED,
                                        self.get_callback_user)
        self.bot.callbacks.set_callback(pymumble.constants.PYMUMBLE_CLBK_SOUNDRECEIVED,
                                        self.get_callback_sound)
        self.bot.callbacks.set_callback(pymumble.constants.PYMUMBLE_CLBK_CHANNELCREATED,
                                        self.get_callback_channel_create)
        self.bot.callbacks.set_callback(pymumble.constants.PYMUMBLE_CLBK_CHANNELUPDATED,
                                        self.get_callback_channel_update)
        self.bot.callbacks.set_callback(pymumble.constants.PYMUMBLE_CLBK_CHANNELREMOVED,
                                        self.get_callback_channel_delete)
        self.bot.callbacks.set_callback(pymumble.constants.PYMUMBLE_CLBK_CONNECTED,
                                        self.get_callback_connected)
        self.bot.callbacks.set_callback(pymumble.constants.PYMUMBLE_CLBK_DISCONNECTED,
                                        self.get_callback_diconnected)

        self.stream_lock = threading.RLock()
        self.stream_frames = {}
        self.stream_last_frames = {}
        self.stream_users = {}

        self.process = process
        self.listening = False
        self.context = {"keep_listening": False}

    def check_and_register(self):
        if self.key_file:
            if "user_id" not in self.bot.users.myself:
                self.log.info("Registerd myself.")
                self.bot.users.myself.register()

    def connect(self):
        self.bot.start()
        self.bot.is_ready()
        self.bot.set_loop_rate(self.pymumble_loop_rate)
        self.start()

        self.check_and_register()

        self.log.debug("loop rate at: {}".format(self.bot.get_loop_rate()))
        if not any(self.bot.users[user]["name"] == self.follow for user in self.bot.users):
            self.move_home()

    def disconnect(self):
        self.running = False
        self.bot.stop()

    def send_to_channel(self, message, channel):
        send_message = ""
        if isinstance(message, list):
            for elem in message:
                send_message += "<br />" + elem
        else:
            send_message = message

        if channel:
            channel.send_text_message(send_message)
        else:
            self.bot.my_channel().send_text_message(send_message)

    def move_to_name(self, channel_name):
        self.log.debug("try to moved to channel_name {}".format(channel_name))
        try:
            while not self.connected:
                time.sleep(0.01)

            channel = self.bot.channels.find_by_name(channel_name)
            channel.move_in()
            time.sleep(0.1)  # ok for now, but check for callback
            self.log.debug("moved to channel {}".format(self.bot.my_channel()))
        except pymumble.errors.UnknownChannelError as err:
            self.log.error(err)

    def move_to_channel(self, channel):
        self.log.debug("try to moved to channel {}".format(channel))
        try:
            while not self.connected:
                time.sleep(0.01)

            channel.move_in()
            time.sleep(0.1)  # ok for now, but check for callback
            self.log.debug("moved to channel {}".format(channel))
        except pymumble.errors.UnknownChannelError as err:
            self.log.error(err)

    def move_home(self):
        self.move_to_name(self.home)

    def move_user(self, user, channel):
        channel.move_in(user["session"])
        self.log.debug("move user {} to channel {}".format(user.name, channel.name))

    def get_callback_user(self, user, changes=None):
        self.log.debug("received user change: {}".format(user))
        if user["name"] == self.follow:
            self.log.debug("follow user: {}".format(user))
            channel = self.bot.channels[user["channel_id"]]
            t = threading.Thread(target=self.move_to_channel, args=(channel,))  # for now
            t.start()

    def get_callback_text(self, text_message: mumble_pb2.TextMessage):
        self.log.debug("received command: {}".format(text_message.message))

        issuing_user = self.bot.users[text_message.actor]
        self.log.debug("issuing_user: {}, tag: {}".format(issuing_user, self.tag))

        if issuing_user["name"] == self.follow and self.tag in text_message.message:
            # todo impelemt some functionality
            channel = self.bot.channels[text_message.channel_id[0]]  # why ever this is a list (maybe global comm?)
            return_str = self.process(text_message.message, self.context)
            self.send_to_channel(return_str, channel)

    def get_callback_sound(self, user, soundchunk):
        session_id = user["session"]
        if user["name"] == self.follow:
            with self.stream_lock:
                if session_id not in self.stream_frames:
                    self.stream_frames[session_id] = []
                    self.stream_users[session_id] = user

                self.stream_frames[session_id].append(numpy.frombuffer(soundchunk.pcm, numpy.int16))
                self.stream_last_frames[session_id] = time.time()  # soundchunk.timestamp does not work

    def get_callback_channel_create(self, channel):
        pass

    def get_callback_channel_update(self, channel, action):
        pass

    def get_callback_channel_delete(self, channel):
        pass

    def get_callback_connected(self):
        self.connected = True

    def get_callback_diconnected(self):
        self.connected = False

    def check_audio(self):
        cur_time = time.time()
        to_process = []
        with self.stream_lock:
            for session_id, old_time in self.stream_last_frames.items():
                if (cur_time - old_time) < self.speech_return_delay or self.stream_frames[session_id] == []:
                    continue
                else:
                    data = numpy.concatenate(self.stream_frames[session_id], axis=0)
                    self.stream_frames[session_id] = []
                    user = self.stream_users[session_id]
                    to_process.append((data, user))

        for data, user in to_process:
            text = self.stt.process_voice(user, data, 48000)
            channel = self.bot.channels[user["channel_id"]]
            issuning_user = user["name"]
            # self.log.debug("recived text \"{}\"".format(text))
            # self.log.debug("\"{}\" == \"{}\"? {}".format(
            #    text.lower(), self.user_name.lower(), text.lower() == self.user_name.lower()))

            text = text.lower().strip()

            if text == self.user_name.lower() or text == self.login_name.lower():
                self.listening = True
                self.send_to_channel("ja?", channel)
            elif self.listening:
                return_str = self.process(text, self.context)
                self.listening = self.context.get("keep_listening", False)
                self.send_to_channel(return_str, channel)

    def run(self):
        self.running = True
        while self.running:
            self.check_audio()
            time.sleep(self.speech_return_delay)
