from abc import ABCMeta, abstractmethod
import typing


class BasicSkill(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def get_key_words(self) -> typing.List[str]:
        pass

    @abstractmethod
    def process(self, text: str, chat_context: dict, global_context: dict, coms: dict) -> typing.Tuple[bool, str]:
        pass

    @abstractmethod
    def gen_help(self) -> typing.List[str]:
        pass
