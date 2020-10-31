from time import sleep
from uuid import uuid4

from config import config

from gmail import Gmail
from persistence import Queue

from loguru import logger


@logger.catch
def main():
    ping = Gmail("../data/credentials.ping.json", "../data/token.ping.pickle", 30000)
    pong = Gmail("../data/credentials.pong.json", "../data/token.pong.pickle", 30001)
    queue = Queue()

    while True:

        # (1) search for pongs
        for uuid_ in queue.queue().copy():
            timestamp = pong.receive_uuid(uuid_)

            if timestamp is None:
                queue.expire(uuid_)
            else:
                queue.receive(uuid_, timestamp)

        # (2) send new pings
        for target in config["targets"]:
            uuid_ = uuid4()
            timestamp = ping.submit_uuid(target, uuid_)
            queue.submit(target, uuid_, timestamp)

        # (3) wait for next round
        wait_for_next_ping()


def wait_for_next_ping():
    wait_time = max(1, 60 // config["pings_per_hour"])
    logger.info("waiting {} minutes ...".format(wait_time))
    sleep(wait_time * 60)


if __name__ == "__main__":
    main()
