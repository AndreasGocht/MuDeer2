from mudeer.skills.weisheiten import Weisheit

weisheiten = Weisheit()


def process(text: str, context: dict):
    if "weisheit" in text:
        return weisheiten.process()
