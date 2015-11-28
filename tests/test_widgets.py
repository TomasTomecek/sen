import pytest
from flexmock import flexmock
from sen.tui.widgets.list.common import ScrollableListBox, AsyncScrollableListBox
from .constants import SCREEN_WIDTH, SCREEN_HEIGHT


class DataGenerator:
    @classmethod
    def text(cls, prefix="line", lines_no=3, return_bytes=False):
        s = "\n".join(["{}{}".format(prefix, x+1) for x in range(lines_no)])
        if return_bytes:
            return s.encode("utf-8")
        return s

    @classmethod
    def stream(cls, prefix="line", lines_no=3, return_bytes=False):
        response = []
        for x in range(lines_no):
            l = "{}{}".format(prefix, x+1)
            if return_bytes:
                l = l.encode("utf-8")
            response.append(l)
        return iter(response)

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
    lb = ScrollableListBox(inp)
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
    assert text == expected
