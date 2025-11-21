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
            self.__set_developers(config)

    def __set_developers(self, config: dict):
        if "developers" in config:
            developers = config["developers"]
        else:
            developers = []
        self.developers = developers

def load_config() -> Config:
    return Config()