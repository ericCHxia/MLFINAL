import yaml


def load_config(config="config.yaml"):
    with open(config) as f:
        return Config(yaml.load(f, Loader=yaml.FullLoader))


class Config:
    def __init__(self, entries: dict = {}):
        for k, v in entries.items():
            if isinstance(v, dict):
                self.__dict__[k] = Config(v)
            else:
                self.__dict__[k] = v
