from time import sleep

import config

from chart import create_chart

import oneagent
from loguru import logger


@logger.catch
def cache(path, last_n_days, sdk):
    while True:  # render, store, wait
        with sdk.trace_custom_service("cacheChart", "PingPongMailMonitor"):
            data = create_chart(last_n_days=last_n_days)
            with open(path, "w") as f:
                f.write(data)
                logger.success(f"successfully pre-cached {path} for last {last_n_days} days")

        # wait 15 minutes
        sleep(15 * 60)


if __name__ == "__main__":
    oneagent.initialize()
    cfg = config.Config(config.CONFIG_PATH)

    cache(
        config.CHART_CACHE_PATH,
        cfg.default_dashboard_days,
        oneagent.get_sdk()
    )
