import logging
import re
import threading
import traceback

import urwid

from sen.tui.widgets.list.base import WidgetBase
from sen.util import _ensure_unicode


logger = logging.getLogger(__name__)


# def translate_asci_sequence(s):
#     # FIXME: not finished
#     translation_map = {
#         "34": "dark blue"
#     }
#     return translation_map.get(s, "")


def strip_from_ansi_esc_sequences(text):
    """
    find ANSI escape sequences in text and remove them

    :param text: str
    :return: list, should be passed to ListBox
    """
    # esc[ + values + control character
    # h, l, p commands are complicated, let's ignore them
    seq_regex = r"\x1b\[[0-9;]*[mKJusDCBAfH]"
    regex = re.compile(seq_regex)
    start = 0
    response = ""
    for match in regex.finditer(text):
        end = match.start()
        response += text[start:end]

        start = match.end()
    response += text[start:len(text)]
    return response


# def colorize_text(text):
#     """
#     finds ANSI color escapes in text and transforms them to urwid
#
#     :param text: str
#     :return: list, should be passed to ListBox
#     """
#     # FIXME: not finished
#     response = []
#     # http://ascii-table.com/ansi-escape-sequences.php
#     regex_pattern = r"(?:\x1b\[(\d+)?(?:;(\d+))*m)([^\x1b]+)"  # [%d;%d;...m
#     regex = re.compile(regex_pattern, re.UNICODE)
#     for match in regex.finditer(text):
#         groups = match.groups()
#         t = groups[-1]
#         color_specs = groups[:-1]
#         urwid_spec = translate_asci_sequence(color_specs)
#         if urwid_spec:
#             item = (urwid.AttrSpec(urwid_spec, "main_list_dg"), t)
#         else:
#             item = t
#         item = urwid.AttrMap(urwid.Text(t, align="left", wrap="any"), "main_list_dg", "main_list_white")
#         response.append(item)
#     return response


class ScrollableListBox(WidgetBase):
    def __init__(self, ui, text, focus_bottom=True):
        self.walker = urwid.SimpleFocusListWalker([])
        super().__init__(ui, self.walker)
        self.set_text(text)
        if focus_bottom:
            try:
                self.set_focus(len(self.walker) - 2)
            except IndexError:
                pass

    def set_text(self, text):
        self.walker.clear()
        text = _ensure_unicode(text)
        # logger.debug(repr(text))
        text = strip_from_ansi_esc_sequences(text)
        list_of_texts = text.split("\n")
        self.walker[:] = [
            urwid.AttrMap(urwid.Text(t.rstrip(), align="left", wrap="any"), "main_list_dg", "main_list_white")
            for t in list_of_texts
        ]


class AsyncScrollableListBox(WidgetBase):
    def __init__(self, generator, ui, static_data=None):
        self.log_texts = []
        if static_data:
            static_data = _ensure_unicode(static_data).split("\n")
            for d in static_data:
                log_entry = d.rstrip()
                if log_entry:
                    self.log_texts.append(urwid.Text(("main_list_dg", log_entry),
                                                     align="left", wrap="any"))
        walker = urwid.SimpleFocusListWalker(self.log_texts)
        super(AsyncScrollableListBox, self).__init__(ui, walker)
        walker.set_focus(len(walker) - 1)

        def fetch_logs():
            line_w = urwid.AttrMap(
                urwid.Text("", align="left", wrap="any"), "main_list_dg", "main_list_white"
            )
            walker.append(line_w)

            while True:
                try:
                    line = next(generator)
                except StopIteration:
                    logger.info("no more logs")
                    line_w = urwid.AttrMap(
                        urwid.Text("No more logs.", align="left", wrap="any"),
                        "main_list_dg", "main_list_white"
                    )
                    walker.append(line_w)
                    walker.set_focus(len(walker) - 1)
                    break
                except Exception as ex:
                    logger.error(traceback.format_exc())
                    ui.notify_message("Error while fetching logs: %s", ex)
                    break
                line = _ensure_unicode(line)
                if self.stop.is_set():
                    break
                if self.filter_query:
                    if self.filter_query not in line:
                        continue
                line_w.original_widget.set_text(line_w.original_widget.text + line.rstrip("\r\n"))
                if line.endswith("\n"):
                    walker.set_focus(len(walker) - 1)
                    line_w = urwid.AttrMap(
                        urwid.Text("", align="left", wrap="any"), "main_list_dg", "main_list_white"
                    )
                    walker.append(line_w)
                ui.refresh()

        self.stop = threading.Event()
        self.thread = threading.Thread(target=fetch_logs, daemon=True)
        self.thread.start()

    def destroy(self):
        self.stop.set()

