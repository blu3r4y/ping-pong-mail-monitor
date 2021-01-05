from time import sleep

from config import CHART_CACHE_PATH

from chart import create_chart

from loguru import logger


def cache(path):
    # render, store, wait
    while True:
        jzon = create_chart()
        with open(path, "w") as f:
            f.write(jzon)
            logger.success("successfully pre-cached {}".format(path))

        # wait 15 minutes
        sleep(15 * 60)


if __name__ == "__main__":
    cache(CHART_CACHE_PATH)
