# -*- coding: utf-8 -*-
import time
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime, timedelta

from flexmock import flexmock

from sen.util import _ensure_unicode, log_traceback, log_vars_from_tback, repeater, humanize_time, \
    OrderedSet

import pytest


@pytest.mark.parametrize("inp,expected", [
    ("a", "a"),
    (b"a", "a"),
    ("\u2606", "☆"),
    (b'\xe2\x98\x86', "☆"),
])
def test_ensure_unicode(inp, expected):
    assert _ensure_unicode(inp) == expected


def test_log_traceback(caplog):
    @log_traceback
    def f():
        raise Exception()
    f()
    assert caplog.records()[0].message.endswith(" is about to be started")
    assert caplog.records()[1].message.startswith("Traceback")
    assert caplog.records()[1].message.endswith("Exception\n")


def test_log_traceback_without_tb(caplog):
    @log_traceback
    def f():
        pass
    f()
    assert caplog.records()[0].message.endswith(" is about to be started")
    assert caplog.records()[1].message.endswith(" finished")


def test_log_traceback_threaded(caplog):
    @log_traceback
    def f():
        raise Exception()

    e = ThreadPoolExecutor(max_workers=1)
    f = e.submit(f)
    while f.running():
        time.sleep(0.1)

    assert caplog.records()[0].message.endswith(" is about to be started")
    assert caplog.records()[1].message.startswith("Traceback")
    assert caplog.records()[1].message.endswith("Exception\n")


def test_log_vars_from_tback(caplog):
    a = 1
    b = None
    c = []
    try:
        raise Exception()
    except Exception:
        log_vars_from_tback(4)

    def has_similar_message(msg):
        for log_entry in caplog.records():
            if msg in log_entry.message:
                return True
        return False

    assert has_similar_message("c = []")
    assert has_similar_message("b = None")
    assert has_similar_message("a = 1")


def test_repeater():
    def g(l, item=1):
        l.append(1)
        return l[item]

    assert repeater(g, args=([], )) == 1
    with pytest.raises(Exception):
        repeater(f, args=([], ), kwargs={"item": 10}) == 1


@pytest.mark.parametrize("inp,expected", [
    (timedelta(seconds=1), "now"),
    (timedelta(seconds=2), "2 seconds ago"),
    (timedelta(seconds=59), "59 seconds ago"),
    (timedelta(minutes=1), "1 minute ago"),
    (timedelta(minutes=1, seconds=1), "1 minute ago"),
    (timedelta(minutes=1, seconds=59), "1 minute ago"),
    (timedelta(minutes=2), "2 minutes ago"),
    (timedelta(minutes=59, seconds=59), "59 minutes ago"),
    (timedelta(minutes=60), "1 hour ago"),
    (timedelta(hours=1), "1 hour ago"),
    (timedelta(hours=1, minutes=59, seconds=59), "1 hour ago"),
    (timedelta(hours=2), "2 hours ago"),
    (timedelta(hours=23, minutes=59, seconds=59), "23 hours ago"),
    (timedelta(hours=24), "1 day ago"),
    (timedelta(days=1, hours=23, minutes=59, seconds=59), "1 day ago"),
    (timedelta(hours=48), "2 days ago"),
    (timedelta(days=29, hours=23, minutes=59, seconds=59), "29 days ago"),
    (timedelta(days=30), "1 month ago"),
    (timedelta(days=59, hours=23, minutes=59, seconds=59), "1 month ago"),
    (timedelta(days=60), "2 months ago"),
])
def test_humanize_time(inp, expected):
    # flexmock(datetime, now=datetime(year=2000, month=1, day=1))
    n = datetime.now()
    assert humanize_time(n - inp) == expected


def test_ordered_set():
    s = OrderedSet()
    s.append(1)
    assert s == [1]
    s.append(2)
    assert s == [1, 2]
    s.append(1)
    assert s == [2, 1]
