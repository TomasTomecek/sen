import sys
import logging


__version__ = "0.1"


def set_logging(name="sen", level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if level == logging.DEBUG:
        handler = logging.FileHandler("debug.log")
    else:
        handler = logging.StreamHandler(sys.stderr)

    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
