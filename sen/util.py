import os
import logging
import functools
import traceback
import time
from datetime import datetime

from docker.errors import APIError

from sen.constants import PROJECT_NAME, LOG_FILE_NAME


logger = logging.getLogger(__name__)


def _ensure_unicode(s):
    try:
        return s.decode("utf-8")
    except AttributeError:
        return s


def log_last_traceback():
    logger.error(traceback.format_exc())


def log_traceback(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info("function %s is about to be started", func)
        try:
            response = func(*args, **kwargs)
        except Exception:
            log_last_traceback()
        else:
            logger.info("function %s finished", func)
            # TODO: how long it took?
            return response
    return wrapper


def setup_dirs():
    """Make required directories to hold logfile.

    :returns: str
    """
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


def humanize_time(value):
    abbrevs = (
        (1, "now"),
        (2, "{seconds} seconds ago"),
        (59, "{seconds} seconds ago"),
        (60, "{minutes} minute ago"),
        (119, "{minutes} minute ago"),
        (120, "{minutes} minutes ago"),
        (3599, "{minutes} minutes ago"),
        (3600, "{hours} hour ago"),
        (7199, "{hours} hour ago"),
        (86399, "{hours} hours ago"),
        (86400, "{days} day ago"),
        (172799, "{days} day ago"),
        (172800, "{days} days ago"),
        (172800, "{days} days ago"),
        (2591999, "{days} days ago"),
        (2592000, "{months} month ago"),
        (5183999, "{months} month ago"),
        (5184000, "{months} months ago"),
    )
    n = datetime.now()
    delta = n - value
    for guard, message in abbrevs:
        s = int(delta.total_seconds())
        if guard >= s:
            break
    return message.format(seconds=delta.seconds, minutes=int(delta.seconds // 60),
                          hours=int(delta.seconds // 3600), days=delta.days,
                          months=int(delta.days // 30))


# # This function is able to crash python b/c it may write monster-amount of data.
# #   Use it only for debugging, do not ship it!
# def log_vars_from_tback(process_frames=5):
#     for th in threading.enumerate():
#         try:
#             thread_frames = sys._current_frames()[th.ident]
#         except KeyError:
#             continue
#         logger.debug(''.join(traceback.format_stack(thread_frames)))
#
#     logger.error(traceback.format_exc())
#     if process_frames <= 0:
#         return
#     tb = sys.exc_info()[2]
#     while 1:
#         if not tb.tb_next:
#             break
#         tb = tb.tb_next
#     stack = []
#     f = tb.tb_frame
#     while f:
#         stack.append(f)
#         f = f.f_back
#     for frame in stack[:process_frames]:
#         logger.debug("frame %s:%s", frame.f_code.co_filename, frame.f_lineno)
#         for key, value in frame.f_locals.items():
#             try:
#                 logger.debug("%20s = %s", key, value)
#             except Exception:
#                 logger.debug("%20s = CANNOT PRINT VALUE", key)
#
#             # self_instance = frame.f_locals.get("self", None)
#             # if not self_instance:
#             #     continue
#             # for key in dir(self_instance):
#             #     if key.startswith("__"):
#             #         continue
#             #     try:
#             #         value = getattr(self_instance, key, None)
#             #         logger.debug("%20s = %s", "self." + key, value)
#             #     except Exception:
#             #         logger.debug("%20s = CANNOT PRINT VALUE", "self." + key)


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

# again taken directly from docker:
#   https://github.com/docker/cli/blob/2bfac7fcdafeafbd2f450abb6d1bb3106e4f3ccb/cli/command/container/stats_helpers.go#L168
# precpu_stats in 1.13+ is completely broken, doesn't contain any values
def calculate_cpu_percent2(d, previous_cpu, previous_system):
    # import json
    # du = json.dumps(d, indent=2)
    # logger.debug("XXX: %s", du)
    cpu_percent = 0.0
    cpu_total = float(d["cpu_stats"]["cpu_usage"]["total_usage"])
    cpu_delta = cpu_total - previous_cpu
    cpu_system = float(d["cpu_stats"]["system_cpu_usage"])
    system_delta = cpu_system - previous_system
    online_cpus = d["cpu_stats"].get("online_cpus", len(d["cpu_stats"]["cpu_usage"]["percpu_usage"]))
    if system_delta > 0.0:
        cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0
    return cpu_percent, cpu_system, cpu_total


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


def calculate_network_bytes(d):
    """

    :param d:
    :return: (received_bytes, transceived_bytes), ints
    """
    networks = graceful_chain_get(d, "networks")
    if not networks:
        return 0, 0
    r = 0
    t = 0
    for if_name, data in networks.items():
        logger.debug("getting stats for interface %r", if_name)
        r += data["rx_bytes"]
        t += data["tx_bytes"]
    return r, t


def graceful_chain_get(d, *args, default=None):
    t = d
    for a in args:
        try:
            t = t[a]
        except (KeyError, ValueError, TypeError, AttributeError):
            logger.debug("can't get %r from %s", a, t)
            return default
    return t


def repeater(call, args=None, kwargs=None, retries=4):
    """
    repeat call x-times: docker API is just awesome

    :param call: function
    :param args: tuple, args for function
    :param kwargs: dict, kwargs for function
    :param retries: int, how many times we try?
    :return: response of the call
    """
    args = args or ()
    kwargs = kwargs or {}
    t = 1.0
    for x in range(retries):
        try:
            return call(*args, **kwargs)
        except APIError as ex:
            logger.error("query #%d: docker returned an error: %r", x, ex)
        except Exception as ex:
            # this may be pretty bad
            log_last_traceback()
            logger.error("query #%d: generic error: %r", x, ex)
        t *= 2
        time.sleep(t)


class OrderedSet(list):
    def append(self, p_object):
        if p_object in self:
            self.remove(p_object)
        return super().append(p_object)

