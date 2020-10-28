from pprint import pprint
from uuid import uuid4

from config import config
from gmail import Gmail

from loguru import logger


@logger.catch
def main():
    g = Gmail()
    for target in config["targets"]:
        g.submit_uuid(target, uuid4())
        pprint(g.receive_uuid("809e6cbd-c442-483f-80fb-875bcac3332f"))


if __name__ == "__main__":
    main()
