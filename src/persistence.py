import time
import pickledb

from config import config

from loguru import logger


class Queue:
    def __init__(self) -> None:
        self.db = pickledb.load("../data/queue.json", auto_dump=True)
        self._startup()

    def queue(self):
        return self.db.lgetall("queue")

    def submit(self, target, uuid, sent_timestamp):
        uuid = str(uuid)

        # track this message
        self.db.dcreate(uuid)
        self.db.dadd(uuid, ("sent", sent_timestamp))
        self.db.dadd(uuid, ("mailbox", target))

        # and add it to the worker queue
        self.db.ladd("queue", uuid)

        logger.info("ping -> {} -> {} (at: {}ms)".format(uuid, target, sent_timestamp))

    def receive(self, uuid, recv_timestamp):
        uuid = str(uuid)

        # track receival of this message
        self.db.dadd(uuid, ("recv", recv_timestamp))

        # compute latency in milliseconds
        target = self.db.dget(uuid, "mailbox")
        sent_timestamp = self.db.dget(uuid, "sent")
        latency = int(recv_timestamp - sent_timestamp)

        # store latency
        ldict = "latency:{}".format(target)
        self.db.dadd(ldict, (recv_timestamp, latency))

        # remove this uuid from the worker queue and the dict metadata
        self.db.lremvalue("queue", uuid)
        self.db.drem(uuid)

        logger.success(
            "pong <- {} (at: {}ms) [latency: {:.1f}s]".format(uuid, recv_timestamp, latency / 1000)
        )

    def expire(self, uuid):
        uuid = str(uuid)

        # check if there even is something expirable
        if not self.db.lexists("queue", uuid):
            return

        # email sent timestamp in minutes
        sent_timestamp = int(self.db.dget(uuid, "sent")) / 1000 / 60
        # utc now timestamp in minutes
        now_timestamp = time.time() / 60

        delta = now_timestamp - sent_timestamp
        if delta > config["receive_timeout"]:
            logger.warning(
                "expired uuid {} in queue because no mail was received since {} minutes".format(
                    uuid, int(delta)
                )
            )

            # expire uuid from queue
            self.db.lremvalue("queue", uuid)

    def _startup(self):
        # possibly create the worker queue
        if not self.db.exists("queue"):
            self.db.lcreate("queue")
            logger.debug("initialized empty queue in pickledb")

        # possible create the latency stores
        for target in config["targets"]:
            ldict = "latency:{}".format(target)
            if not self.db.exists(ldict):
                self.db.dcreate(ldict)
                logger.debug("initialized empty latency store '{}' in pickledb".format(ldict))