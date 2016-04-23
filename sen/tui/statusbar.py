import logging
import threading

import urwid
from sen.tui.constants import CLEAR_NOTIF_BAR_MESSAGE_IN
from sen.tui.widgets.util import ThreadSafeFrame
from sen.util import log_traceback


logger = logging.getLogger(__name__)


class UIFrameWidget(ThreadSafeFrame):
    """
    wrapper class for all statusbar/notifbar related methods
    """

    def __init__(self, ui, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = ui

        # widget -> message or None
        self.widget_message_dict = {}
        # message -> widget
        self.message_widget_dict = {}
        self.status_bar = None
        self.prompt_bar = None

        # lock when managing notifications:
        #  * when accessing self.notification_*
        #  * when accessing widgets
        # and most importantly, remember, locking is voodoo
        self.notifications_lock = threading.RLock()

    def reload_footer(self, refresh=True, rebuild_statusbar=True):
        logger.debug("reload footer")
        footer = list(self.widget_message_dict.keys())
        if self.prompt_bar:
            footer.append(self.prompt_bar)
        else:
            if rebuild_statusbar or self.status_bar is None:
                self.status_bar = self.build_statusbar()
            footer.append(self.status_bar)
        # logger.debug(footer)
        self.set_footer(urwid.Pile(footer))
        if refresh:
            self.ui.refresh()

    def build_statusbar(self):
        """construct and return statusbar widget"""
        try:
            left_widgets = self.ui.current_buffer.build_status_bar() or []
        except AttributeError:
            left_widgets = []
        text_list = []
        for idx, buffer in enumerate(self.ui.buffers):
            #  #1 [I] fedora #2 [L]
            fmt = "#{idx} [{tag}] {name}"
            markup = fmt.format(idx=idx, tag=buffer.tag, name=buffer.display_name)
            text_list.append((
                "status_box_focus" if buffer == self.ui.current_buffer else "status_box",
                markup,
            ))
            text_list.append(" ")
        text_list = text_list[:-1]

        if text_list:
            buffer_text = urwid.Text(text_list, align="right")
        else:
            buffer_text = urwid.Text("", align="right")
        columns = urwid.Columns(left_widgets + [buffer_text])
        return urwid.AttrMap(columns, "status")

    def prompt(self, prompt_text, callback):
        """
        prompt for text input.
        """
        oldfooter = self.get_footer()

        # set up widgets
        leftpart = urwid.Text(prompt_text, align='left')
        editpart = urwid.Edit(multiline=True)

        # build promptwidget
        edit = urwid.Columns(
            [
                ('fixed', len(prompt_text), leftpart),
                ('weight', 1, editpart),
            ])
        self.prompt_bar = urwid.AttrMap(edit, "main_list_dg")

        self.reload_footer()
        self.set_focus("footer")

        urwid.connect_signal(editpart, "change", callback, user_args=[self.ui, oldfooter])

    def remove_notification_message(self, message):
        logger.debug("requested remove of message %r from notif bar", message)
        with self.notifications_lock:
            try:
                w = self.message_widget_dict[message]
            except KeyError:
                logger.warning("there is no notification %r displayed", message)
                return
            else:
                logger.debug("remove widget %r from new pile", w)
                del self.widget_message_dict[w]
                del self.message_widget_dict[message]
        self.reload_footer(rebuild_statusbar=False)

    def remove_widget(self, widget, message=None):
        logger.debug("remove widget %r from notif bar", widget)
        with self.notifications_lock:
            del self.widget_message_dict[widget]
            if message:
                del self.message_widget_dict[message]
        self.reload_footer(rebuild_statusbar=False)

    def notify_message(self, message, level="info", clear_if_dupl=True,
                       clear_in=CLEAR_NOTIF_BAR_MESSAGE_IN):
        """
        :param message, str
        :param level: str, {info, error}
        :param clear_if_dupl: bool, if True, don't display the notification again
        :param clear_in: seconds, remove the notificantion after some time

        opens notification popup.
        """
        with self.notifications_lock:
            if clear_if_dupl and message in self.message_widget_dict.keys():
                logger.debug("notification %r is already displayed", message)
                return
            logger.debug("display notification %r", message)
            widget = urwid.AttrMap(urwid.Text(message), "notif_{}".format(level))
        return self.notify_widget(widget, clear_in=clear_in)

    def notify_widget(self, widget, message=None, clear_in=CLEAR_NOTIF_BAR_MESSAGE_IN):
        """
        opens notification popup.

        :param widget: instance of Widget, widget to display
        :param message: str, message to remove from list of notifications
        :param clear_in: int, time seconds when notification should be removed
        """

        @log_traceback
        def clear_notification(*args, **kwargs):
            # the point here is the log_traceback
            self.remove_widget(widget, message=message)

        if not widget:
            return

        logger.debug("display notification widget %s", widget)

        with self.notifications_lock:
            self.widget_message_dict[widget] = message
            if message:
                self.message_widget_dict[message] = widget

        self.reload_footer(rebuild_statusbar=False)
        self.ui.set_alarm_in(clear_in, clear_notification)

        return widget
