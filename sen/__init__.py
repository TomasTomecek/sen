import logging


__version__ = "0.1"


def set_logging(name="sen", level=logging.DEBUG):
    # create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = logging.FileHandler("debug.log")
    handler.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    handler.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(handler)


set_logging(level=logging.WARNING)  # override this however you want
