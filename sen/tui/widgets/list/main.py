import logging
import re
import threading

import urwid

from sen.exceptions import NotifyError
from sen.docker_backend import DockerImage, DockerContainer
from sen.tui.widgets.list.util import (
    get_map, get_time_attr_map, get_operation_notify_widget, ResponsiveRowWidget
)
from sen.tui.widgets.table import ResponsiveTable
from sen.tui.widgets.util import SelectableText
from sen.util import log_traceback


logger = logging.getLogger(__name__)


def get_detailed_image_row(docker_image):
    row = []
    image_id = SelectableText(docker_image.short_id, maps=get_map())
    row.append(image_id)

    command = SelectableText(docker_image.command, maps=get_map(defult="main_list_ddg"))
    row.append(command)

    base_image = docker_image.base_image()
    base_image_text = ""
    if base_image:
        base_image_text = base_image.short_name
    base_image_w = SelectableText(base_image_text, maps=get_map())
    row.append(base_image_w)

    time = SelectableText(docker_image.display_time_created(),
                          maps=get_time_attr_map(docker_image.created))
    row.append(time)

    image_names_markup = get_image_names_markup(docker_image)
    # urwid.Text([]) tracebacks
    if image_names_markup:
        image_names = SelectableText(image_names_markup)
    else:
        image_names = SelectableText("")
    row.append(image_names)

    return row


def get_image_names_markup(docker_image):
    text_markup = []
    for n in docker_image.names:
        if n.registry:
            text_markup.append(("main_list_dg", n.registry + "/"))
        if n.namespace and n.repo:
            text_markup.append(("main_list_lg", n.namespace + "/" + n.repo))
        else:
            if n.repo == "<none>":
                text_markup.append(("main_list_dg", n.repo))
            else:
                text_markup.append(("main_list_lg", n.repo))
        if n.tag:
            if n.tag not in ["<none>", "latest"]:
                text_markup.append(("main_list_dg", ":" + n.tag))
        text_markup.append(("main_list_dg", ", "))
    text_markup = text_markup[:-1]
    return text_markup


def get_detailed_container_row(docker_container):
    row = []
    container_id = SelectableText(docker_container.short_id)
    row.append(container_id)

    command = SelectableText(docker_container.command, get_map(defult="main_list_ddg"))
    row.append(command)

    image = SelectableText(docker_container.image_name())
    row.append(image)

    if docker_container.running:
        attr_map = get_map("main_list_green")
    elif docker_container.exited_well:
        attr_map = get_map("main_list_orange")
    elif docker_container.status_created:
        attr_map = get_map("main_list_yellow")
    else:
        attr_map = get_map("main_list_red")
    status = SelectableText(docker_container.status, attr_map)
    row.append(status)

    name = SelectableText(docker_container.short_name)
    row.append(name)

    return row


def get_row(docker_object):
    if isinstance(docker_object, DockerImage):
        return get_detailed_image_row(docker_object)
    elif isinstance(docker_object, DockerContainer):
        return get_detailed_container_row(docker_object)
    else:
        raise Exception("what ")


class MainLineWidget(ResponsiveRowWidget):
    def __init__(self, docker_object):
        self.docker_object = docker_object
        super().__init__(get_row(docker_object))

    # TODO
    def matches_search(self, s):
        return self.docker_object.matches_search(s)

    # TODO
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.docker_object)

    def __str__(self):
        return "{}".format(self.docker_object)


class MainListBox(ResponsiveTable):
    def __init__(self, docker_backend, ui):
        self.d = docker_backend
        self.ui = ui
        super(MainListBox, self).__init__(urwid.SimpleFocusListWalker([]))

        # urwid is not thread safe
        self.refresh_lock = threading.Lock()

        self.thread = threading.Thread(target=self.realtime_updates, daemon=True)
        self.thread.start()

    def populate(self, focus_on_top=False):
        widgets = self._assemble_initial_content()
        with self.refresh_lock:
            self.set_body(widgets)
            self.ro_content = widgets
            if focus_on_top:
                self.set_focus(0)
            self.ui.refresh()

    def realtime_updates(self):
        """
        update listing realtime as events come from docker

        :return:
        """
        for content in self.d.realtime_updates():
            widgets = []
            for o in content:
                try:
                    line = MainLineWidget(o)
                except Exception as ex:
                    logger.error("%r", ex)
                    continue
                widgets.append(line)
            with self.refresh_lock:
                self.set_body(widgets)
                self.ui.reload_footer()

    def _assemble_initial_content(self):
        def query_notify(operation):
            w = get_operation_notify_widget(operation, display_always=False)
            if w:
                self.ui.notify_widget(w)

        rows = []

        query, c_op, i_op = self.d.filter()
        for o in query:
            rows.append(MainLineWidget(o))
        query_notify(i_op)
        query_notify(c_op)

        return rows

    @property
    def focused_docker_object(self):
        try:
            return self.get_focus()[0].docker_object
        except AttributeError as ex:
            raise NotifyError("Can't select focused object")

    def filter(self, s, widgets_to_filter=None):
        s = s.strip()
        if not s:
            self.filter_query = None
            self.populate(focus_on_top=True)
            return

        backend_query = {
            "cached": True,
            "containers": False,
            "images": False,
        }

        def containers():
            backend_query["containers"] = True

        def images():
            backend_query["images"] = True

        def running():
            backend_query["stopped"] = False

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
        query_list = re.split(r"[\s,]", s)
        unprocessed = []
        do_query = False
        for query_str in query_list:
            # process here x=y queries and pass rest to parent filter()
            try:
                query_key, query_value = query_str.split("=", 1)
            except ValueError:
                unprocessed.append(query_str)
            else:
                do_query = True
                logger.debug("looking up query key %r and query value %r", query_key, query_value)
                for c in query_conf:
                    if query_key in c["query_keys"] and query_value in c["query_values"]:
                        c["callback"]()
                        break
                else:
                    raise NotifyError("Invalid query string: %r", query_str)
        if do_query:
            widgets = []
            logger.debug("doing query %s", backend_query)
            query, c_op, i_op = self.d.filter(**backend_query)
            for o in query:
                line = MainLineWidget(o)
                widgets.append(line)
            if unprocessed:
                new_query = " ".join(unprocessed)
                logger.debug("doing parent query for unprocessed string: %r", new_query)
                widgets = super().filter(new_query, widgets_to_filter=widgets)
        else:
            logger.debug("doing parent query: %r", s)
            widgets = super().filter(s)
        self.filter_query = s
        return widgets

    def keypress(self, size, key):
        # FIXME: put this into own file
        # these functions will be executed in threads
        # provide arguments, don't access self.<attrib> b/c those will be
        # evaluated when the code is running, not when calling it
        @log_traceback
        def run_and_report_on_fail(fn_name, docker_object, pre_message,
                                   notif_level="info"):
            self.ui.notify_message(pre_message)
            try:
                operation = getattr(docker_object, fn_name)()
            except AttributeError:
                log_txt = "you can't {} {}".format(fn_name, docker_object)
                logger.error(log_txt)
                notif_txt = "You can't {} {} {!r}.".format(
                    fn_name,
                    docker_object.pretty_object_type.lower(),
                    docker_object.short_name)
                self.ui.notify_message(notif_txt, level="error")
            except Exception as ex:
                self.ui.notify_message(str(ex), level="error")
                raise
            else:
                self.ui.remove_notification_message(pre_message)
                self.ui.notify_widget(
                    get_operation_notify_widget(operation, notif_level=notif_level)
                )
                # we don't need to refresh whole buffer here, since we are getting realtime
                # updates using events call
                # self.ui.refresh_main_buffer()

        @log_traceback
        def do_and_report_on_fail(f, docker_object):
            try:
                if docker_object:
                    f(docker_object)
                else:
                    f()
            except NotifyError as ex:
                self.ui.notify_message(str(ex), level="error")
                logger.error(repr(ex))

        logger.debug("size %r, key %r", size, key)

        try:
            if key == "@":
                self.ui.run_in_background(self.populate, None)
            elif key == "i":
                self.ui.run_in_background(do_and_report_on_fail, self.ui.inspect, self.focused_docker_object)
                return
            elif key == "l":
                self.ui.run_in_background(do_and_report_on_fail, self.ui.display_logs, self.focused_docker_object)
                return
            elif key == "f":
                self.ui.run_in_background(do_and_report_on_fail, self.ui.display_and_follow_logs, self.focused_docker_object)
                return
            elif key == "enter":
                self.ui.run_in_background(do_and_report_on_fail, self.ui.display_info, self.focused_docker_object)
                return
            elif key == "d":
                self.ui.run_in_background(
                    run_and_report_on_fail,
                    "remove",
                    self.focused_docker_object,
                    "Removing {} {}...".format(self.focused_docker_object.pretty_object_type.lower(),
                                               self.focused_docker_object.short_name),
                    notif_level="important"
                )
                return
            elif key == "s":
                self.ui.run_in_background(
                    run_and_report_on_fail,
                    "start",
                    self.focused_docker_object,
                    "Starting container {}...".format(self.focused_docker_object.short_name)
                )
                return
            elif key == "r":
                self.ui.run_in_background(
                    run_and_report_on_fail,
                    "restart",
                    self.focused_docker_object,
                    "Restarting container {}...".format(self.focused_docker_object.short_name)
                )
                return
            elif key == "t":
                self.ui.run_in_background(
                    run_and_report_on_fail,
                    "stop",
                    self.focused_docker_object,
                    "Stopping container {}...".format(self.focused_docker_object.short_name)
                )
                return
            elif key == "p":
                self.ui.run_in_background(
                    run_and_report_on_fail,
                    "pause",
                    self.focused_docker_object,
                    "Pausing container {}...".format(self.focused_docker_object.short_name)
                )
                return
            elif key == "u":
                self.ui.run_in_background(
                    run_and_report_on_fail,
                    "unpause",
                    self.focused_docker_object,
                    "Unpausing container {}...".format(self.focused_docker_object.short_name)
                )
                return
            elif key == "X":
                self.ui.run_in_background(
                    run_and_report_on_fail,
                    "kill",
                    self.focused_docker_object,
                    "Killing container {}...".format(self.focused_docker_object.short_name)
                )
                return
        except NotifyError as ex:
            self.ui.notify_message(str(ex), level="error")
            logger.error(repr(ex))

        key = super(MainListBox, self).keypress(size, key)
        return key

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

        parent_cols = super().status_bar()
        if parent_cols:
            add_subwidget(", ")
        return columns_list + parent_cols
