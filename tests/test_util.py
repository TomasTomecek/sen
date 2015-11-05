# -*- coding: utf-8 -*-
from concurrent.futures.thread import ThreadPoolExecutor
import time

from sen.util import _ensure_unicode, log_traceback

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
    assert caplog.records()[0].message.startswith("starting thread")
    assert caplog.records()[1].message.startswith("Traceback")
    assert caplog.records()[1].message.endswith("Exception\n")


def test_log_traceback_without_tb(caplog):
    @log_traceback
    def f():
        pass
    f()
    assert caplog.records()[0].message.startswith("starting thread")
    assert caplog.records()[1].message.startswith("closing thread")


def test_log_traceback_threaded(caplog):
    @log_traceback
    def f():
        raise Exception()

    e = ThreadPoolExecutor(max_workers=1)
    f = e.submit(f)
    while f.running():
        time.sleep(0.1)

    assert caplog.records()[0].message.startswith("starting thread")
    assert caplog.records()[1].message.startswith("Traceback")
    assert caplog.records()[1].message.endswith("Exception\n")
