import logging
import functools
import traceback


logger = logging.getLogger(__name__)


def _ensure_unicode(s):
    try:
        return s.decode("utf-8")
    except AttributeError:
        return s


def log_traceback(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info("starting thread for function %s", func)
        try:
            response = func(*args, **kwargs)
        except Exception:
            logger.error(traceback.format_exc())
        else:
            logger.info("closing thread for function %s", func)
            return response
    return wrapper
