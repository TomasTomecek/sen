import logging


__version__ = "0.1"


def set_logging(name="sen", level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = logging.FileHandler("debug.log")
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
