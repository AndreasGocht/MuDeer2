import configparser
import pkg_resources
import gettext
import logging
import argparse


from mudeer.main import MuDeer


def main():
    parser = argparse.ArgumentParser(description='MuDeeR')
    parser.add_argument('-c', '--config', help='MuDeeRs config file', nargs=1, required=True)
    args = parser.parse_args()

    # load config
    config = configparser.ConfigParser()
    try:
        with open(args.config[0]) as f:
            config.read_file(f)
    except FileNotFoundError as e:
        logging.fatal("did not find config file:\n{}".format(e))
        exit(-1)

    logging.basicConfig(level=config["logging"].get("level", "INFO"))

    # localisation
    local_path = pkg_resources.resource_filename(__name__, "/locales")
    text = gettext.translation("commands", localedir=local_path, languages=[config["etc"]["lang"]], fallback=True)
    text.install()

    # setup an run
    deer = MuDeer(config)
    deer.connect()
    try:
        deer.run()
    except KeyboardInterrupt:
        pass
    finally:
        deer.disconnect()
