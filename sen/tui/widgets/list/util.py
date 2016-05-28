import datetime
import logging

import urwid

from sen.tui.constants import MAIN_LIST_FOCUS
from sen.tui.widgets.responsive_column import ResponsiveColumns
from sen.tui.widgets.util import SelectableText, get_map


logger = logging.getLogger(__name__)


def get_color_text(markup, color_attr="status_text"):
    w = urwid.AttrMap(urwid.Text(markup), color_attr)
    return len(markup), w


def get_operation_notify_widget(operation, notif_level="info", display_always=True):
    if not operation:
        return
    attr = "notif_{}".format(notif_level)
    took = operation.took
    text_list = []
    if took > 300:
        fmt_str = "{} Query took "
        text_list.append((attr, fmt_str.format(operation.pretty_message)))
        command_took_str = "{:.2f}".format(took)
        if took < 500:
            text_list.append(("notif_text_yellow", command_took_str))
        elif took < 1000:
            text_list.append(("notif_text_orange", command_took_str))
        else:
            command_took_str = "{:.2f}".format(took / 1000.0)
            text_list.append(("notif_text_red", command_took_str))
            text_list.append((attr, " s"))
        if took < 1000:
            text_list.append((attr, " ms"))
    elif display_always:
        text_list.append((attr, operation.pretty_message))
    else:
        return
    return urwid.AttrMap(urwid.Text(text_list), attr)


def get_time_attr_map(t):
    """
                                                       now -> |
                            hour ago -> |
        day ago -> |
    |--------------|--------------------|---------------------|
    """
    now = datetime.datetime.now()
    if t + datetime.timedelta(hours=3) > now:
        return get_map("main_list_white")
    if t + datetime.timedelta(days=3) > now:
        return get_map("main_list_lg")
    else:
        return get_map("main_list_dg")


class UnselectableRowWidget(urwid.AttrMap):
    def __init__(self, columns, attr="main_list_dg", focus_map=MAIN_LIST_FOCUS, dividechars=1):
        self.widgets = columns
        self.columns = urwid.Columns(columns, dividechars=dividechars)
        super().__init__(self.columns, attr, focus_map=focus_map)

    @property
    def contents(self):
        return self.columns.contents

    def render(self, size, focus=False):
        for w in self.columns.widget_list:
            if hasattr(w, "set_map"):
                w.set_map('focus' if focus else 'normal')
        return urwid.AttrMap.render(self, size, focus)


class RowWidget(UnselectableRowWidget):
    def selectable(self):
        return True


class SingleTextRow(RowWidget):
    def __init__(self, text_markup, maps=None):
        super().__init__([SelectableText(text_markup, maps=maps)])


class ResponsiveRowWidget(RowWidget):
    def __init__(self, columns, attr="main_list_dg", focus_map=MAIN_LIST_FOCUS, dividechars=1):
        self.widgets = columns
        self.columns = ResponsiveColumns(columns, dividechars=dividechars)
        urwid.AttrMap.__init__(self, self.columns, attr, focus_map=focus_map)
