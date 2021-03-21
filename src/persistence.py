import re
import time
import pickledb

from shutil import copyfile
from collections import namedtuple

import config

import oneagent
from loguru import logger

# a regex that matches uuid4 strings with and without dashes
UUID4_REGEX = re.compile(
    "[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}", re.I
)


class Queue:
    # a data structure for the delta calculation
    DeltaTuple = namedtuple("DeltaTuple", ["sent", "minutes_difference"])

    def __init__(self, cfg: config.Config) -> None:
        oneagent.initialize()
        self.db = pickledb.load(config.QUEUE_PATH, auto_dump=False)
        self.cfg = cfg
        self.sdk = oneagent.get_sdk()
        self._startup()

    def dump(self):
        copyfile(config.QUEUE_PATH, config.QUEUE_BAK_PATH)  # backup first
        with self.sdk.trace_custom_service("dumpQueue", "PingPongMailMonitor"):
            logger.info("saving queue to disk now ...")
            self.db.dump()

    def queue(self):
        return self.db.lgetall("queue").copy()

    def submit(self, target, uuid, sent_timestamp, auto_dump=True):
        uuid = str(uuid)

        # track this message
        self.db.dcreate(uuid)
        self.db.dadd(uuid, ("sent", int(sent_timestamp)))
        self.db.dadd(uuid, ("mailbox", target))

        # and add it to the worker queue
        self.db.ladd("queue", uuid)

        logger.info("PING -> {} -> {} (at: {}ms)".format(uuid, target, sent_timestamp))

        if auto_dump:
            self.dump()

    def receive(self, uuid, recv_timestamp, auto_dump=True):
        uuid = str(uuid)

        # track receival of this message
        self.db.dadd(uuid, ("recv", int(recv_timestamp)))

        # compute latency in milliseconds
        target = self.db.dget(uuid, "mailbox")
        sent_timestamp = self.db.dget(uuid, "sent")
        latency = int(recv_timestamp - sent_timestamp)

        # store latency
        ldict = self._get_latency_store_key(target)
        self.db.dadd(ldict, (str(sent_timestamp), latency))

        # remove this uuid from the worker queue and the dict metadata
        self.db.lremvalue("queue", uuid)
        self.db.drem(uuid)

        logger.success(
            "PONG <- {} <- {} (at: {}ms) [latency: {:.1f}s]".format(
                uuid, target, recv_timestamp, latency / 1000
            )
        )

        if auto_dump:
            self.dump()

    def expire(self, uuid, auto_dump=True):
        uuid = str(uuid)

        # check if we got metadata on this uuid
        if self.db.exists(uuid):

            delta = self._get_uuid_sent_delta(uuid)
            if delta.minutes_difference > self.cfg.receive_timeout:

                # store this key as expired
                target = self.db.dget(uuid, "mailbox")
                ldict = self._get_latency_store_key(target, auto_dump=auto_dump)
                self.db.dadd(ldict, (str(delta.sent), -1))

                # expire uuid from worker queue
                if self.db.lexists("queue", uuid):
                    self.db.lremvalue("queue", uuid)

                # and flag metadata as expired (keep it for forensic reasons)
                self.db.dadd(uuid, ("expired", "true"))

                logger.warning(
                    "expired uuid {} because no mail was received since {} minutes (limit: {} minutes)".format(
                        uuid,
                        delta.minutes_difference,
                        self.cfg.receive_timeout,
                    )
                )

        # check for a dangling uuid in the queue (should never happen)
        elif self.db.lexists("queue", uuid):
            self.db.lremvalue("queue", uuid)
            logger.error("removed dangling uuid {} from queue".format(uuid))

        if auto_dump:
            self.dump()

    def revoke(self, uuid, auto_dump=True):
        uuid = str(uuid)

        # re-add this to the queue (if it isn't in there already)
        if not self.db.lexists("queue", uuid):
            self.db.ladd("queue", uuid)

        # unset the expired flag
        self.db.dadd(uuid, ("expired", "false"))
        logger.info("re-queued already expired uuid {}".format(uuid))

        if auto_dump:
            self.dump()

    def revoke_all(self):
        for key in list(self.db.getall()):
            if UUID4_REGEX.match(key):
                if self.db.dexists(key, "expired") and self.db.dget(key, "expired") == "true":
                    self.revoke(key, auto_dump=False)

        self.dump()

    def _startup(self):
        # possibly create the worker queue
        if not self.db.exists("queue"):
            self.db.lcreate("queue")
            logger.debug("initialized empty queue in pickledb")

        # possibly create the latency stores
        for target in self.cfg.targets:
            self._get_latency_store_key(target, auto_dump=False)

        # possibly re-queue dangling, put not yet expired uuids that are not in the queue
        for key in list(self.db.getall()):
            if UUID4_REGEX.match(key):
                if not self.db.dexists(key, "expired") and not self.db.lexists("queue", key):
                    self.db.ladd("queue", key)
                    logger.warning("re-queued dangling uuid {}".format(key))

        self.dump()

    def _get_latency_store_key(self, target, auto_dump=True):
        ldict = "latency:{}".format(target)

        # possibly create the store if it doesn't exist already
        if not self.db.exists(ldict):
            self.db.dcreate(ldict)
            logger.debug("initialized empty latency store '{}' in pickledb".format(ldict))

        if auto_dump:
            self.dump()

        return ldict

    def _get_uuid_sent_delta(self, uuid):
        # email sent timestamp in ms
        sent_timestamp = int(self.db.dget(uuid, "sent"))
        # utc now timestamp in minutes
        now_timestamp = time.time() / 60

        # time difference in minutes
        delta = now_timestamp - (sent_timestamp / 1000 / 60)

        return self.DeltaTuple(sent=int(sent_timestamp), minutes_difference=int(delta))
