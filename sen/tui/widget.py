import datetime
import logging
import threading

import urwid
from sen.exceptions import NotifyError

from sen.tui.constants import MAIN_LIST_FOCUS
from sen.docker_backend import DockerImage, DockerContainer


logger = logging.getLogger(__name__)


class AdHocAttrMap(urwid.AttrMap):
    """
    Ad-hoc attr map change

    taken from https://github.com/pazz/alot/
    """
    def __init__(self, w, maps, init_map='normal'):
        self.maps = maps
        urwid.AttrMap.__init__(self, w, maps[init_map])

    def set_map(self, attrstring):
        self.set_attr_map({None: self.maps[attrstring]})


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
                base_image_text = base_image.short_name.to_str()
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
        super().__init__(self.columns, "normal", focus_map=MAIN_LIST_FOCUS)

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


class ScrollableListBox(urwid.ListBox):
    def __init__(self, text):
        text = urwid.Text(("text", text), align="left", wrap="any")
        body = urwid.SimpleFocusListWalker([text])
        super(ScrollableListBox, self).__init__(body)


class AsyncScrollableListBox(urwid.ListBox):
    def __init__(self, generator, ui, static_data=None):
        self.log_texts = []
        if static_data:
            for d in static_data.decode("utf-8").split("\n"):
                log_entry = d.strip()
                if log_entry:
                    self.log_texts.append(urwid.Text(("text", log_entry), align="left", wrap="any"))
        walker = urwid.SimpleFocusListWalker(self.log_texts)
        super(AsyncScrollableListBox, self).__init__(walker)

        def fetch_logs():
            for line in generator:
                if self.stop.is_set():
                    break
                walker.append(urwid.Text(("text", line.strip()), align="left", wrap="any"))
                walker.set_focus(len(walker) - 1)
                ui.refresh()

        self.stop = threading.Event()
        self.thread = threading.Thread(target=fetch_logs, daemon=True)
        self.thread.start()

    def destroy(self):
        self.stop.set()


class MainListBox(urwid.ListBox):
    def __init__(self, docker_backend, ui):
        self.d = docker_backend
        self.ui = ui
        self.walker = urwid.SimpleFocusListWalker([])
        super(MainListBox, self).__init__(self.walker)

    def populate(self, focus_on_top=False):
        widgets = self._assemble_initial_content()
        self.walker[:] = widgets
        if focus_on_top:
            self.set_focus(0)

    def _assemble_initial_content(self):
        widgets = []
        for o in self.d.initial_content():
            line = MainLineWidget(o)
            widgets.append(line)
        return widgets

    @property
    def focused_docker_object(self):
        return self.get_focus()[0].docker_object

    def keypress(self, size, key):
        def run_and_report_on_fail(f, message, notif_level="info"):
            logger.debug("running command %r for key %r", f.__name__, key)
            try:
                f()
            except AttributeError:
                notif_txt = "You can't {} {} {}.".format(
                    f.__name__,
                    self.focused_docker_object.pretty_object_type.lower(),
                    self.focused_docker_object.short_name)
                log_txt = "you can't {} {}".format(f.__name__, self.focused_docker_object)
                logger.error(log_txt)
                self.ui.notify(notif_txt, level="error")
            except Exception as ex:
                logger.error(repr(ex))
                self.ui.notify(str(ex), level="error")
            else:
                self.ui.notify(message, level=notif_level)
            self.ui.refresh_main_buffer()

        def do_and_report_on_fail(f):
            try:
                f(self.focused_docker_object)
            except NotifyError as ex:
                self.ui.notify(str(ex), level="error")
                logger.error(repr(ex))

        logger.debug("size %r, key %r", size, key)
        if key == "i":
            do_and_report_on_fail(self.ui.inspect)
            return
        elif key == "l":
            do_and_report_on_fail(self.ui.display_logs)
            return
        elif key == "f":
            do_and_report_on_fail(self.ui.display_and_follow_logs)
            return
        elif key == "d":
            run_and_report_on_fail(self.focused_docker_object.remove,
                                   "{} {} removed!".format(
                                       self.focused_docker_object.pretty_object_type,
                                       self.focused_docker_object.short_name),
                                   "error")
            return
        elif key == "s":
            run_and_report_on_fail(self.focused_docker_object.start,
                                   "Container {} started.".format(
                                       self.focused_docker_object.short_name))
            return
        elif key == "r":
            run_and_report_on_fail(self.focused_docker_object.restart,
                                   "Container {} restarted.".format(
                                       self.focused_docker_object.short_name))
            return
        elif key == "t":
            run_and_report_on_fail(self.focused_docker_object.stop,
                                   "Container {} stopped.".format(
                                       self.focused_docker_object.short_name))
            return
        elif key == "p":
            run_and_report_on_fail(self.focused_docker_object.pause,
                                   "Container {} paused.".format(
                                       self.focused_docker_object.short_name))
            return
        elif key == "u":
            run_and_report_on_fail(self.focused_docker_object.unpause,
                                   "Container {} unpaused.".format(
                                       self.focused_docker_object.short_name))
            return
        elif key == "X":
            run_and_report_on_fail(self.focused_docker_object.kill,
                                   "Container {} killed.".format(
                                       self.focused_docker_object.short_name))
            return
        elif key == "j":
            return super().keypress(size, "down")
        elif key == "k":
            return super().keypress(size, "up")
        key = super(MainListBox, self).keypress(size, key)
        return key
