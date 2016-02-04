# from concurrent.futures.thread import ThreadPoolExecutor
import logging
import threading

import urwid
from sen.tui.constants import CLEAR_NOTIF_BAR_MESSAGE_IN
from sen.util import log_traceback


logger = logging.getLogger(__name__)


class Footer:
    """
    wrapper class for all statusbar/notifbar related methods
    """

    def __init__(self, ui):
        self.ui = ui
        self.notif_bar = None
        self.status_bar = self.build_statusbar()
        self.prompt_bar = None
        self.notifications = []

        # lock when managing notifications:
        #  * when accessing self.notifications
        #  * when accessing widgets
        # and most importantly, remember, locking is voodoo
        # FIXME: Rlock may be better
        self.notifications_lock = threading.Lock()
        # urwid is not thread safe, so changing data and rendering needs to be atomic
        self.refresh_lock = threading.Lock()

    def reload_footer(self, refresh=True, rebuild_statusbar=True):
        logger.debug("reload footer")
        bottom = []
        if self.notif_bar:
            bottom.append(self.notif_bar)
        if self.prompt_bar:
            bottom.append(self.prompt_bar)
        else:
            if rebuild_statusbar:
                self.status_bar = self.build_statusbar()
            bottom.append(self.status_bar)
        with self.refresh_lock:
            self.ui.set_footer(urwid.Pile(bottom))
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
        oldfooter = self.ui.mainframe.get_footer()

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

        widgets = []
        if self.notif_bar:
            widgets.append(self.notif_bar)
        widgets.append(self.prompt_bar)
        self.ui.mainframe.set_footer(urwid.Pile(widgets))

        self.ui.mainframe.set_focus("footer")

        urwid.connect_signal(editpart, "change", callback, user_args=[self.ui, oldfooter])

    def remove_notification_message(self, message):
        logger.debug("requested remove of message %r from notif bar", message)
        with self.notifications_lock:
            if message in self.notifications:
                self.notifications.remove(message)
            if self.notif_bar:
                newpile = self.notif_bar.widget_list
                for w in newpile:
                    if w.original_widget.get_text()[0] == message:
                        logger.debug("remove widget %r from new pile", w)
                        newpile.remove(w)
                        break
                if newpile:
                    self.notif_bar = urwid.Pile(newpile)
                else:
                    self.notif_bar = None
            else:
                self.notif_bar = None
        self.reload_footer(rebuild_statusbar=False)

    def notify_message(self, message=None, level="info", clear_if_dupl=True,
                        clear_in=CLEAR_NOTIF_BAR_MESSAGE_IN):
        """
        :param level: str, {info, error}

        opens notification popup.
        """
        with self.notifications_lock:
            if clear_if_dupl and message in self.notifications:
                logger.debug("notification %r is already displayed", message)
                return
            self.notifications.append(message)
        logger.debug("display notification %r", message)
        widget = urwid.AttrMap(urwid.Text(message), "notif_{}".format(level))
        self.notify_widget(widget, message=message, clear_in=clear_in)

    def notify_widget(self, widget, message=None, clear_in=CLEAR_NOTIF_BAR_MESSAGE_IN):
        """
        opens notification popup.

        :param widget: instance of Widget, widget to display
        :param message: str, message to remove from list of notifications
        :param clear_in: int, time seconds when notification should be removed
        """

        @log_traceback
        def clear_notification(*args, **kwargs):
            # time.sleep(clear_in)
            logger.debug("remove widget %r from notif bar", widget)
            with self.notifications_lock:
                if message in self.notifications:
                    self.notifications.remove(message)
                if self.notif_bar:
                    newpile = self.notif_bar.widget_list
                    if widget in newpile:
                        newpile.remove(widget)
                    if newpile:
                        self.notif_bar = urwid.Pile(newpile)
                    else:
                        self.notif_bar = None
                else:
                    self.notif_bar = None
            self.reload_footer(rebuild_statusbar=False)

        if not widget:
            return

        logger.debug("display notification widget %s", widget)

        widget_list = [widget]
        with self.notifications_lock:
            # stack errors, don't overwrite them
            if not self.notif_bar:
                self.notif_bar = urwid.Pile(widget_list)
            else:
                logger.debug(self.notif_bar.widget_list)
                newpile = self.notif_bar.widget_list + widget_list
                self.notif_bar = urwid.Pile(newpile)

        self.reload_footer(rebuild_statusbar=False)
        self.ui.set_alarm_in(clear_in, clear_notification)
