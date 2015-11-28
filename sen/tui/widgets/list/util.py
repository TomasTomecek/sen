import datetime
import logging

import urwid

from sen.tui.constants import MAIN_LIST_FOCUS


logger = logging.getLogger(__name__)


def get_color_text(markup, color_attr="status_text"):
    w = urwid.AttrMap(urwid.Text(markup), color_attr)
    return len(markup), w


def get_operation_notify_widget(operation, notif_level="info", display_always=True):
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


def get_map(defult="main_list_dg"):
    return {"normal": defult, "focus": MAIN_LIST_FOCUS}


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

