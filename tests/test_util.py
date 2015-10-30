# -*- coding: utf-8 -*-
from sen.util import _ensure_unicode

import pytest


@pytest.mark.parametrize("inp,expected", [
    ("a", "a"),
    (b"a", "a"),
    ("\u2606", "☆"),
    (b'\xe2\x98\x86', "☆"),
])
def test_ensure_unicode(inp, expected):
    assert _ensure_unicode(inp) == expected
