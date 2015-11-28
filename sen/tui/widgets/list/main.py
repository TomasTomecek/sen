import logging
import re
import threading

import urwid
from sen.exceptions import NotifyError

from sen.tui.constants import MAIN_LIST_FOCUS
from sen.docker_backend import DockerImage, DockerContainer
from sen.tui.widgets.list.base import VimMovementListBox
from sen.tui.widgets.list.util import get_map, get_time_attr_map, get_operation_notify_widget
from sen.tui.widgets.util import AdHocAttrMap
from sen.util import log_traceback


logger = logging.getLogger(__name__)


class MainLineWidget(urwid.AttrMap):
    FIRST_COL = 12
    THIRD_COL = 16
    FOURTH_COL = 30

    def __init__(self, o):
        self.docker_object = o
        self.widgets = []
        columns = []

        if isinstance(o, DockerImage):
            image_id = AdHocAttrMap(urwid.Text(o.image_id[:12]), get_map())
            self.widgets.append(image_id)
            columns.append((self.FIRST_COL, image_id))

            command = AdHocAttrMap(urwid.Text(o.command, wrap="clip"),
                                   get_map(defult="main_list_ddg"))
            self.widgets.append(command)
            columns.append(command)

            base_image = o.base_image()
            base_image_text = ""
            if base_image:
                base_image_text = base_image.short_name
            base_image_w = AdHocAttrMap(urwid.Text(base_image_text, wrap="clip"), get_map())
            self.widgets.append(base_image_w)
            columns.append((self.THIRD_COL, base_image_w))

            time = AdHocAttrMap(urwid.Text(o.display_time_created()), get_time_attr_map(o.created))
            self.widgets.append(time)
            columns.append((self.FOURTH_COL, time))

            names_widgets = []

            def add_subwidget(markup, color_attr):
                w = AdHocAttrMap(urwid.Text(markup), get_map(color_attr))
                names_widgets.append((len(markup), w))
                self.widgets.append(w)

            for n in o.names:
                if n.registry:
                    add_subwidget(n.registry + "/", "main_list_dg")
                if n.namespace and n.repo:
                    add_subwidget(n.namespace + "/" + n.repo, "main_list_lg")
                else:
                    if n.repo == "<none>":
                        add_subwidget(n.repo, "main_list_dg")
                    else:
                        add_subwidget(n.repo, "main_list_lg")
                if n.tag:
                    if n.tag not in ["<none>", "latest"]:
                        add_subwidget(":" + n.tag, "main_list_dg")
                add_subwidget(", ", "main_list_dg")
            names_widgets = names_widgets[:-1]
            names = AdHocAttrMap(urwid.Columns(names_widgets), get_map())
            self.widgets.append(names)
            columns.append(names)

        elif isinstance(o, DockerContainer):
            container_id = AdHocAttrMap(urwid.Text(o.container_id[:12]), get_map())
            self.widgets.append(container_id)
            columns.append((12, container_id))

            command = AdHocAttrMap(urwid.Text(o.command, wrap="clip"),
                                   get_map(defult="main_list_ddg"))
            self.widgets.append(command)
            columns.append(command)

            image = AdHocAttrMap(urwid.Text(o.image_name()), get_map())
            self.widgets.append(image)
            columns.append((self.THIRD_COL, image))

            if o.status.startswith("Up"):
                attr_map = get_map("main_list_green")
            elif o.status.startswith("Exited (0)"):
                attr_map = get_map("main_list_orange")
            elif o.status.startswith("Created"):
                attr_map = get_map("main_list_yellow")
            else:
                attr_map = get_map("main_list_red")
            status = AdHocAttrMap(urwid.Text(o.status), attr_map)
            self.widgets.append(status)
            columns.append((self.FOURTH_COL, status))

            name = AdHocAttrMap(urwid.Text(o.short_name, wrap="clip"), get_map())
            self.widgets.append(name)
            columns.append(name)

        self.columns = urwid.Columns(columns, dividechars=1)
        super().__init__(self.columns,
                         "main_list_dg",
                         focus_map=MAIN_LIST_FOCUS)

    def matches_search(self, s):
        return self.docker_object.matches_search(s)

    def selectable(self):
        return True

    def render(self, size, focus=False):
        for w in self.widgets:
            w.set_map('focus' if focus else 'normal')
        return urwid.AttrMap.render(self, size, focus)

    def keypress(self, size, key):
        logger.debug("%r keypress, focus: %s", self, self.focus)
        return key

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.docker_object)

    def __str__(self):
        return "{}".format(self.docker_object)


class MainListBox(VimMovementListBox):
    def __init__(self, docker_backend, ui):
        self.d = docker_backend
        self.ui = ui
        self.walker = urwid.SimpleFocusListWalker([])
        super(MainListBox, self).__init__(self.walker)

        self.thread = threading.Thread(target=self.realtime_updates, daemon=True)
        self.thread.start()

    def populate(self, focus_on_top=False):
        widgets = self._assemble_initial_content()
        self.walker[:] = widgets
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
            self.walker[:] = widgets
            self.ui.reload_footer()
            self.ui.refresh()

    def _assemble_initial_content(self):
        def query_notify(operation):
            w = get_operation_notify_widget(operation, display_always=False)
            if w:
                self.ui.notify_widget(w)

        widgets = []
        query, c_op, i_op = self.d.filter()
        for o in query:
            line = MainLineWidget(o)
            widgets.append(line)
        query_notify(i_op)
        query_notify(c_op)
        return widgets

    @property
    def focused_docker_object(self):
        try:
            return self.get_focus()[0].docker_object
        except AttributeError as ex:
            raise NotifyError("Nothing selected!")

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
                self.ui.run_in_background(do_and_report_on_fail, self.ui.display_image_info, self.focused_docker_object)
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
