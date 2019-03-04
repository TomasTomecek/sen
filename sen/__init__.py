import logging

from sen.constants import FALLBACK_LOG_PATH

__version__ = '0.6.1'


def set_logging(name="sen", level=logging.DEBUG, path=FALLBACK_LOG_PATH):
    logger = logging.getLogger(name)
    # do not propagate logs from logger 'sen' to root logger (as they could be accidentally
    # displayed in terminal)
    logger.propagate = False
    logger.setLevel(level)

    handler = logging.FileHandler(path)
    handler.setLevel(logging.DEBUG)
    # handler = logging.StreamHandler(sys.stderr)

    formatter = logging.Formatter(
        '%(asctime)s.%(msecs).03d %(filename)-17s %(levelname)-6s %(message)s', '%H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
