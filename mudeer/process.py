from mudeer.skills.weisheiten import Weisheit

weisheiten = Weisheit()


def process(text: str, chat_context: dict, global_context: dict, coms: dict) -> str:
    if "weisheit" in text:
        return weisheiten.process()
