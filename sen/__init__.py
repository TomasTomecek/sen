import sys
import logging


__version__ = "0.1"


def set_logging(name="sen", level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if level == logging.DEBUG:
        handler = logging.FileHandler("debug.log")
        handler.setLevel(logging.DEBUG)
    # else:
    #     handler = logging.StreamHandler(sys.stderr)

        formatter = logging.Formatter('%(asctime)s %(name)-18s %(levelname)-6s %(message)s',
                                      '%H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
