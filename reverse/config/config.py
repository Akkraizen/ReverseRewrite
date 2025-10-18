import json

from reverse.structure.singleton import Singleton


class Config(Singleton):
    def __init__(self):
        if not self.created:
            config = {}
            with open("../config/config.json", mode="r") as configfile:
                config.update(json.load(configfile))
                configfile.close()

            self.token = config["token"]

def load_config() -> Config:
    return Config()