import logging
import random
from itertools import chain

import pytest
from flexmock import flexmock
from urwid.listbox import SimpleListWalker

from sen.tui.widgets.list.base import WidgetBase
from sen.tui.widgets.list.common import ScrollableListBox, AsyncScrollableListBox
from sen.tui.widgets.list.util import ResponsiveRowWidget
from sen.tui.widgets.table import ResponsiveTable, assemble_rows
from .utils import get_random_text_widget
from .constants import SCREEN_WIDTH, SCREEN_HEIGHT


class MockUI:
    buffers = []

    def refresh(self):
        pass

    def set_alarm_in(self, *args, **kwargs):
        pass


class DataGenerator:
    @classmethod
    def text(cls, prefix="line", lines_no=3, return_bytes=False):
        s = "\n".join(["{}{}".format(prefix, x+1) for x in range(lines_no)])
        if return_bytes:
            return s.encode("utf-8")
        return s

    @classmethod
    def stream(cls, prefix="line", lines_no=3, return_bytes=False):
        text = []
        for x in range(lines_no):
            l = "{}{}\n".format(prefix, x+1)
            if return_bytes:
                l = l.encode("utf-8")
            text.append(l)
        s = chain(text)
        return iter(s)

    @classmethod
    def render(cls, prefix="line", lines_no=3, return_bytes=True):
        w = "{:%d}" % SCREEN_WIDTH
        response = []
        for x in range(SCREEN_HEIGHT):
            if x >= lines_no:
                l = w.format("")
            else:
                l = w.format("{}{}".format(prefix, x+1))
            if return_bytes:
                response.append(l.encode("utf-8"))
            else:
                response.append(l)
        return response


@pytest.mark.parametrize("inp,expected", [
    (DataGenerator.text(), DataGenerator.render()),
    (DataGenerator.text(return_bytes=True), DataGenerator.render()),
    (DataGenerator.text(prefix="liné"), DataGenerator.render(prefix="liné")),
    (DataGenerator.text(prefix="liné", return_bytes=True), DataGenerator.render(prefix="liné")),
])
def test_scrollable_listbox(inp, expected):
    lb = ScrollableListBox(MockUI(), inp)
    canvas = lb.render((SCREEN_WIDTH, SCREEN_HEIGHT))
    text = [bytes().join([t for at, cs, t in ln]) for ln in canvas.content()]
    assert text == expected


@pytest.mark.parametrize("inp,expected", [
    (DataGenerator.stream(), DataGenerator.render()),
    (DataGenerator.stream(return_bytes=True), DataGenerator.render()),
    (DataGenerator.stream(prefix="liné"), DataGenerator.render(prefix="liné")),
    (DataGenerator.stream(prefix="liné", return_bytes=True), DataGenerator.render(prefix="liné")),
])
def test_async_scrollable_listbox(inp, expected):
    ui = flexmock(refresh=lambda: None)
    lb = AsyncScrollableListBox(inp, ui)
    lb.thread.join()
    canvas = lb.render((SCREEN_WIDTH, SCREEN_HEIGHT))
    text = [bytes().join([t for at, cs, t in ln]) for ln in canvas.content()]
    w = "{:%d}" % SCREEN_WIDTH
    s = w.format("{}".format("No more logs."))
    expected[4] = s.encode("utf-8")
    assert text == expected


def test_table_random_data():
    rows = [ResponsiveRowWidget([get_random_text_widget(random.randint(2, 9)) for _ in range(5)])
            for _ in range(5)]
    table = ResponsiveTable(MockUI(), SimpleListWalker(rows))
    canvas = table.render((80, 20), focus=False)
    text = [bytes().join([t for at, cs, t in ln]) for ln in canvas.content()]
    logging.info("%r", text)
    assert len(text) == 20
    assert text[0].startswith(rows[0].original_widget.widget_list[0].text.encode("utf-8"))


def test_table_empty():
    rows = []
    table = ResponsiveTable(MockUI(), SimpleListWalker(rows))
    canvas = table.render((80, 20), focus=False)
    text = [bytes().join([t for at, cs, t in ln]) for ln in canvas.content()]
    assert len(text) == 20
    assert text[0] == b" " * 80


def test_assemble_rows_long_text():
    rows = [[get_random_text_widget(10),
             get_random_text_widget(300)] for _ in range(5)]
    assembled_rows = assemble_rows(rows, ignore_columns=[1])
    lb = WidgetBase(MockUI(), SimpleListWalker(assembled_rows))
    canvas = lb.render((80, 20), focus=False)
    text = [bytes().join([t for at, cs, t in ln]) for ln in canvas.content()]
    logging.info("%r", text)
    assert len(text) == 20
    first_col, second_col = text[0].split(b" ", 1)
    assert first_col == rows[0][0].text.encode("utf-8")
    assert rows[0][1].text.encode("utf-8").startswith(second_col)
