import logging

import urwid

from sen.tui.widgets.list.base import WidgetBase
from sen.tui.widgets.list.util import RowWidget

logger = logging.getLogger(__name__)


def calculate_max_cols_length(table, size):
    """
    :param table: list of lists:

    [["row 1 column 1", "row 1 column 2"],
     ["row 2 column 1", "row 2 column 2"]]

    each item consists of instance of urwid.Text

    :returns dict, {index: width}
    """
    max_cols_lengths = {}

    for row in table:
        col_index = 0
        for idx, widget in enumerate(row.widgets):
            l = widget.pack((size[0], ))[0]
            max_cols_lengths[idx] = max(max_cols_lengths.get(idx, 0), l)
            col_index += 1

    max_cols_lengths.setdefault(0, 1)  # in case table is empty
    return max_cols_lengths


def assemble_rows(data, max_allowed_lengths=None, dividechars=1,
                  ignore_columns=None):
    """
    :param data: list of lists:
    [["row 1 column 1", "row 1 column 2"],
     ["row 2 column 1", "row 2 column 2"]]
    each item consists of instance of urwid.Text

    :param max_allowed_lengths: dict:
        {col_index: maximum_allowed_length}
    :param ignore_columns: list of ints, indexes which should not be calculated
    """
    rows = []
    max_lengths = {}
    ignore_columns = ignore_columns or []

    # shitty performance, here we go
    # it would be way better to do a single double loop and provide mutable variable
    # FIXME: merge this code with calculate() from above
    for row in data:
        col_index = 0
        for widget in row:
            if col_index in ignore_columns:
                continue
            l = len(widget.text)
            if max_allowed_lengths:
                if col_index in max_allowed_lengths and max_allowed_lengths[col_index] < l:
                    # l is bigger then what is allowed
                    l = max_allowed_lengths[col_index]

            max_lengths.setdefault(col_index, l)
            max_lengths[col_index] = max(l, max_lengths[col_index])
            col_index += 1

    for row in data:
        row_widgets = []
        for idx, item in enumerate(row):
            if idx in ignore_columns:
                row_widgets.append(item)
            else:
                row_widgets.append((max_lengths[idx], item))
        rows.append(
            RowWidget(row_widgets, dividechars=dividechars)
        )

    return rows


class ResponsiveTable(WidgetBase):
    def __init__(self, ui, walker, headers=None, dividechars=1, responsive=True):
        """
        :param walker: list of ResponsiveRow instances
        :param headers: list of widgets which should be displayed as headers
        """
        self.dividechars = dividechars
        self.responsive = responsive

        super().__init__(ui, walker)

    def render(self, size, focus=False):
        screen_width = size[0]

        # max text length for each column -- table
        min_col_lengths = calculate_max_cols_length(self.body, size)

        # compute maximal column width -- looks nicer
        max_col_width = int(screen_width / len(min_col_lengths)) - self.dividechars
        for k, v in min_col_lengths.items():
            min_col_lengths[k] = min(min_col_lengths[k], max_col_width)

        columns_occupy = sum(min_col_lengths.values())

        if self.responsive:
            # responsibility! spread the columns
            to_spread = screen_width - len(min_col_lengths) * self.dividechars - columns_occupy
            if to_spread:
                spread_remaining = to_spread
                weights = {}  # longer cols will get more space
                sum_weights = 0
                sorted_by_length = sorted(min_col_lengths.items(), key=lambda x: x[1])
                longest_col = sorted_by_length[-1][0]
                for weight, (idx, length) in enumerate(sorted_by_length):
                    weights[idx] = weight + 1  # first weight is 1; 0 doesn't add anything
                    sum_weights += weight + 1
                for k, v in min_col_lengths.items():
                    expansion = int(to_spread * weights[k] / sum_weights)
                    min_col_lengths[k] += expansion
                    spread_remaining -= expansion
                # add remaining to the longest col
                min_col_lengths[longest_col] += spread_remaining

        for row in self.body:
            row.contents[:] = [
                (w, (urwid.GIVEN, min_col_lengths[idx], is_box))
                for idx, (w, (_, _, is_box)) in enumerate(row.contents)
            ]

        return super().render(size, focus=focus)
