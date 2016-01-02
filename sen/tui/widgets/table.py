import logging

import urwid

from sen.tui.widgets.list.base import VimMovementListBox
from sen.tui.widgets.list.util import RowWidget

logger = logging.getLogger(__name__)


def assemble_rows(data, headers=None):
    """
    :param data: list of lists:
    [["row 1 column 1", "row 1 column 2"],
     ["row 2 column 1", "row 2 column 2"]]

    each item consists of instance of urwid.Text
    """
    rows = []
    max_lengths = []

    # shitty performance, here we go
    # it would be way better to do a single double loop and provide mutable variable
    for row in data:
        col_index = 0
        for widget in row:
            l = len(widget.text)
            try:
                max_lengths[col_index] = max(l, max_lengths[col_index])
            except IndexError:
                max_lengths.append(l)
            col_index += 1

    if headers:
        header_widgets = []
        for header in headers:
            try:
                header_widgets.append(urwid.Text(*header[0], **header[1]))
            except IndexError:
                header_widgets.append(urwid.Text(*header[0]))
        rows.append(urwid.Columns(header_widgets, dividechars=1))

    for row in data:
        rows.append(
                RowWidget([(max_lengths[idx], item) for idx, item in enumerate(row)])
        )

    return rows


class ResponsiveTable(VimMovementListBox):
    def __init__(self, data, headers=None):
        """
        :param headers: list of widgets which should be displayed as headers
        :param data: list of lists:
            [["row 1 column 1", "row 1 column 2"],
             ["row 2 column 1", "row 2 column 2"]]

             each item consists of instance of urwid.Text
        """

        self.walker = urwid.SimpleFocusListWalker(assemble_rows(data, headers=headers))

        super().__init__(self.walker)
