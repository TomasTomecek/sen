import os
import sys
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


def humanize_bytes(bytesize, precision=2):
    """
    Humanize byte size figures

    https://gist.github.com/moird/3684595
    """
    abbrevs = (
        (1 << 50, 'PB'),
        (1 << 40, 'TB'),
        (1 << 30, 'GB'),
        (1 << 20, 'MB'),
        (1 << 10, 'kB'),
        (1, 'bytes')
    )
    if bytesize == 1:
        return '1 byte'
    for factor, suffix in abbrevs:
        if bytesize >= factor:
            break
    if factor == 1:
        precision = 0
    return '%.*f %s' % (precision, bytesize / float(factor), suffix)


def log_vars_from_tback(process_frames=5):
    logger.error(traceback.format_exc())
    tb = sys.exc_info()[2]
    while 1:
        if not tb.tb_next:
            break
        tb = tb.tb_next
    stack = []
    f = tb.tb_frame
    while f:
        stack.append(f)
        f = f.f_back
    stack.reverse()  # top most frame will be on the bottom of a log file
    for frame in stack[:process_frames]:
        logger.debug("frame %s:%s", frame.f_code.co_filename, frame.f_lineno)
        for key, value in frame.f_locals.items():
            try:
                logger.debug("%20s = %s", key, value)
            except Exception:
                logger.debug("%20s = CANNOT PRINT VALUE", key)

            self_instance = frame.f_locals.get("self", None)
            if not self_instance:
                continue
            for key in dir(self_instance):
                if key.startswith("__"):
                    continue
                try:
                    value = getattr(self_instance, key, None)
                    logger.debug("%20s = %s", "self." + key, value)
                except Exception:
                    logger.debug("%20s = CANNOT PRINT VALUE", "self." + key)


# this is taken directly from docker client:
#   https://github.com/docker/docker/blob/28a7577a029780e4533faf3d057ec9f6c7a10948/api/client/stats.go#L309
def calculate_cpu_percent(d):
    cpu_count = len(d["cpu_stats"]["cpu_usage"]["percpu_usage"])
    cpu_percent = 0.0
    cpu_delta = float(d["cpu_stats"]["cpu_usage"]["total_usage"]) - \
                float(d["precpu_stats"]["cpu_usage"]["total_usage"])
    system_delta = float(d["cpu_stats"]["system_cpu_usage"]) - \
                   float(d["precpu_stats"]["system_cpu_usage"])
    if system_delta > 0.0:
        cpu_percent = cpu_delta / system_delta * 100.0 * cpu_count
    return cpu_percent


def calculate_blkio_bytes(d):
    """

    :param d:
    :return: (read_bytes, wrote_bytes), ints
    """
    bytes_stats = graceful_chain_get(d, "blkio_stats", "io_service_bytes_recursive")
    if not bytes_stats:
        return 0, 0
    r = 0
    w = 0
    for s in bytes_stats:
        if s["op"] == "Read":
            r += s["value"]
        elif s["op"] == "Write":
            w += s["value"]
    return r, w


def graceful_chain_get(d, *args, default=None):
    t = d
    for a in args:
        try:
            t = t[a]
        except (KeyError, ValueError, TypeError) as ex:
            logger.debug("can't get %r from %s", a, t)
            return default
    return t
