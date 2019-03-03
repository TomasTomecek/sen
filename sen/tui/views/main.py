import logging
import re
import threading
import time

import urwid

from sen.exceptions import NotifyError, NotAvailableAnymore
from sen.tui.chunks.misc import get_row
from sen.tui.widgets.list.util import (
    get_operation_notify_widget, ResponsiveRowWidget
)
from sen.tui.widgets.table import ResponsiveTable
from sen.util import graceful_chain_get

logger = logging.getLogger(__name__)


class MainLineWidget(ResponsiveRowWidget):
    def __init__(self, docker_object):
        self.docker_object = docker_object
        super().__init__(get_row(docker_object))

    def matches_search(self, s):
        return self.docker_object.matches_search(s)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.docker_object)

    def __str__(self):
        return "{}".format(self.docker_object)


class MainListBox(ResponsiveTable):
    def __init__(self, ui, docker_backend):
        self.d = docker_backend
        super(MainListBox, self).__init__(ui, urwid.SimpleFocusListWalker([]))

        # urwid is not thread safe
        self.refresh_lock = threading.Lock()

        # realtime lock
        self.realtime_lock = threading.Lock()

        self.stop_realtime_events = threading.Event()

    def refresh(self, query=None):
        """
        refresh listing, also apply filters
        :return:
        """
        logger.info("refresh listing")
        focus_on_top = len(self.body) == 0  # focus if empty
        with self.refresh_lock:
            self.query(query_string=query)
        if focus_on_top:
            try:
                self.set_focus(0)
            except IndexError:
                pass

    def process_realtime_event(self, event):
        with self.realtime_lock:
            if self.stop_realtime_events.is_set():
                logger.info("received docker event when this functionality is disabled")
                return
        delayed_events = ["pause", "unpause"]
        ev_status = graceful_chain_get(event, "status")
        if ev_status in delayed_events:
            # https://github.com/TomasTomecek/sen/issues/143
            # tl;dr dockerd does not tell us when the container is in pause/unpause state
            # it sends the event when the container is being paused
            time.sleep(1)
        self.refresh(query=self.filter_query)

    def filter(self, s, widgets_to_filter=None):
        self.refresh(query=s)

    def toggle_realtime_events(self):
        with self.realtime_lock:
            if self.stop_realtime_events.is_set():
                self.stop_realtime_events.clear()
                self.ui.notify_message("Enabling live updates from docker.")
            else:
                self.stop_realtime_events.set()
                self.ui.notify_message("Disabling live updates from docker.")
        self.ui.reload_footer()

    def query(self, query_string=""):
        """
        query and display, also apply filters

        :param query_string: str
        :return: None
        """

        def query_notify(operation):
            w = get_operation_notify_widget(operation, display_always=False)
            if w:
                self.ui.notify_widget(w)

        if query_string is not None:
            self.filter_query = query_string.strip()

        # FIXME: this could be part of filter command since it's command line
        backend_query = {
            "cached": False,
            "containers": True,
            "images": True,
        }

        def containers():
            backend_query["containers"] = True
            backend_query["images"] = not backend_query["images"]
            backend_query["cached"] = True

        def images():
            backend_query["containers"] = not backend_query["containers"]
            backend_query["images"] = True
            backend_query["cached"] = True

        def running():
            backend_query["stopped"] = False
            backend_query["cached"] = True
            backend_query["images"] = False

        query_conf = [
            {
                "query_keys": ["t", "type"],
                "query_values": ["c", "container", "containers"],
                "callback": containers
            }, {
                "query_keys": ["t", "type"],
                "query_values": ["i", "images", "images"],
                "callback": images
            }, {
                "query_keys": ["s", "state"],
                "query_values": ["r", "running"],
                "callback": running
            },
        ]
        query_list = re.split(r"[\s,]", self.filter_query)
        unprocessed = []
        for query_str in query_list:
            if not query_str:
                continue
            # process here x=y queries and pass rest to parent filter()
            try:
                query_key, query_value = query_str.split("=", 1)
            except ValueError:
                unprocessed.append(query_str)
            else:
                logger.debug("looking up query key %r and query value %r", query_key, query_value)
                for c in query_conf:
                    if query_key in c["query_keys"] and query_value in c["query_values"]:
                        c["callback"]()
                        break
                else:
                    raise NotifyError("Invalid query string: %r", query_str)

        widgets = []
        logger.debug("doing query %s", backend_query)
        query, c_op, i_op = self.d.filter(**backend_query)

        for o in query:
            try:
                line = MainLineWidget(o)
            except NotAvailableAnymore:
                continue
            widgets.append(line)
        if unprocessed:
            new_query = " ".join(unprocessed)
            logger.debug("doing parent query for unprocessed string: %r", new_query)
            super().filter(new_query, widgets_to_filter=widgets)
        else:
            self.set_body(widgets)
            self.ro_content = widgets

        query_notify(i_op)
        query_notify(c_op)

    def status_bar(self):
        columns_list = []

        def add_subwidget(markup, color_attr=None):
            if color_attr is None:
                w = urwid.AttrMap(urwid.Text(markup), "status_text")
            else:
                w = urwid.AttrMap(urwid.Text(markup), color_attr)
            columns_list.append((len(markup), w))

        add_subwidget("Images: ")
        images_count = len(self.d.get_images(cached=True).response)
        if images_count < 10:
            add_subwidget(str(images_count), "status_text_green")
        elif images_count < 50:
            add_subwidget(str(images_count), "status_text_yellow")
        else:
            add_subwidget(str(images_count), "status_text_orange")

        add_subwidget(", Containers: ")
        containers_count = len(self.d.get_containers(cached=True, stopped=True).response)
        if containers_count < 5:
            add_subwidget(str(containers_count), "status_text_green")
        elif containers_count < 30:
            add_subwidget(str(containers_count), "status_text_yellow")
        elif containers_count < 100:
            add_subwidget(str(containers_count), "status_text_orange")
        else:
            add_subwidget(str(containers_count), "status_text_red")

        add_subwidget(", Running: ")
        running_containers = self.d.get_containers(cached=True, stopped=False).response
        running_containers_n = len(running_containers)
        add_subwidget(str(running_containers_n),
                      "status_text_green" if running_containers_n > 0 else "status_text")

        with self.realtime_lock:
            if self.stop_realtime_events.is_set():
                add_subwidget(", Live updates are disabled")

        parent_cols = super().status_bar()
        if parent_cols:
            add_subwidget(", ")
        return columns_list + parent_cols
