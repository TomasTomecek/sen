import os
import logging
import functools
import traceback

from sen.constants import PROJECT_NAME, LOG_FILE_NAME

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


def setup_dirs():
    try:
        top_dir = os.path.abspath(os.path.expanduser(os.environ["XDG_CACHE_HOME"]))
    except KeyError:
        top_dir = os.path.abspath(os.path.expanduser("~/.cache"))
    our_cache_dir = os.path.join(top_dir, PROJECT_NAME)
    os.makedirs(our_cache_dir, mode=0o775, exist_ok=True)
    return our_cache_dir


def get_log_file_path():
    return os.path.join(setup_dirs(), LOG_FILE_NAME)
