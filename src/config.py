import json

from loguru import logger

# just load the config dictionary
with open("../data/config.json", "r") as f:
    data = f.read()
config = json.loads(data)

logger.success("successfully parsed config.json")
logger.info(config)
