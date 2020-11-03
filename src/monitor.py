from time import sleep
from uuid import uuid4

import config

from gmail import Gmail
from persistence import Queue

from loguru import logger


@logger.catch
def main():
    # initialize the configuration singleton
    cfg = config.Config(config.CONFIG_PATH)
    ping = Gmail(cfg, "../data/credentials.ping.json", "../data/token.ping.pickle", auth_port=0)
    pong = Gmail(cfg, "../data/credentials.pong.json", "../data/token.pong.pickle", auth_port=0)
    queue = Queue(cfg)

    while True:

        # re-load configuration online
        cfg.reload()

        # (1) search for pongs
        for uuid_ in queue.queue():
            timestamp = pong.receive_uuid(uuid_)

            if timestamp is None:
                queue.expire(uuid_)
            else:
                queue.receive(uuid_, timestamp)

        # (2) send new pings
        for target in cfg.targets:
            uuid_ = uuid4()
            timestamp = ping.submit_uuid(target, uuid_)
            queue.submit(target, uuid_, timestamp)
            wait_for_next_ping(cfg.pings_per_hour, len(cfg.targets))


def wait_for_next_ping(pings_per_hour, num_targets):
    wait_time = int((max(1, 60 // pings_per_hour) / num_targets) * 60)
    logger.info("waiting {} seconds ...".format(wait_time))
    sleep(wait_time)


if __name__ == "__main__":
    main()
