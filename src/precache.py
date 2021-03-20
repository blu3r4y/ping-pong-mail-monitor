from time import sleep

from config import CHART_CACHE_PATH

from chart import create_chart

import oneagent
from loguru import logger

oneagent.initialize()
sdk = oneagent.get_sdk()


@logger.catch
def cache(path):
    while True:  # render, store, wait
        with sdk.trace_custom_service("cacheChart", "PingPongMailMonitor"):
            jzon = create_chart()
            with open(path, "w") as f:
                f.write(jzon)
                logger.success("successfully pre-cached {}".format(path))

        # wait 15 minutes
        sleep(15 * 60)


if __name__ == "__main__":
    cache(CHART_CACHE_PATH)
