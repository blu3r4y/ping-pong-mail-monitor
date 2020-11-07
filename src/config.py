import json

from loguru import logger

CONFIG_PATH = r"../data/config.json"
QUEUE_PATH =  r"../data/queue.json"


class Config:
    class __ConfigSingleton:
        def __init__(self, path) -> None:
            self.path = path
            self._obj = None
            self.reload()

        def __getattr__(self, name):
            if self._obj is None:
                raise ValueError("no config loaded")
            return self._obj[name]

        def reload(self):
            # just load the config dictionary
            with open(self.path, "r") as f:
                data = f.read()
            self._obj = json.loads(data)

            logger.success("successfully parsed config.json")
            logger.info(self._obj)

    instance = None

    def __init__(self, path=None):
        if not Config.instance:
            # grab the existing instance
            if path is None:
                raise ValueError("the Config object must be initialized with a path at least once")
            Config.instance = Config.__ConfigSingleton(path)
        else:
            # adjust the path and reload the config
            if path is not None:
                Config.instance.path = path
                Config.instance.reload()

    def __getattr__(self, name):
        return getattr(self.instance, name)
