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


class VimMovementListBox(urwid.ListBox):
    """
    ListBox with vim-like movement which can be inherited in other widgets
    """
    def __init__(self, *args, **kwargs):
        # we want "gg"!
        self.cached_key = None
        self.search_string = None
        super().__init__(*args, **kwargs)

    def reload_widget(self):
        # this is the easiest way to refresh body
        self.body[:] = self.body

    def _search(self, reverse_search=False):
        if self.search_string is None:
            raise NotifyError("No search pattern specified.")
        pos = self.focus_position
        while True:
            if reverse_search:
                obj, pos = self.body.get_prev(pos)
            else:
                obj, pos = self.body.get_next(pos)
            if obj is None:
                raise NotifyError("Pattern not found: %r." % self.search_string)
            if self.search_string in obj.original_widget.text:
                self.set_focus(pos)
                self.reload_widget()
                break

    def find_previous(self, search_pattern=None):
        if search_pattern is not None:
            self.search_string = search_pattern
        self._search(reverse_search=True)

    def find_next(self, search_pattern=None):
        if search_pattern is not None:
            self.search_string = search_pattern
        self._search()

    def keypress(self, size, key):
        logger.debug("VimListBox keypress %r", key)

        # FIXME: workaround so we allow "gg" only, and not "g*"
        if self.cached_key == "g" and key != "g":
            self.cached_key = None

        if key == "j":
            return super().keypress(size, "down")
        elif key == "k":
            return super().keypress(size, "up")
        elif key == "ctrl d":
            try:
                self.set_focus(self.get_focus()[1] + 10)
            except IndexError:
                self.set_focus(len(self.body) - 1)
            self.reload_widget()
            return
        elif key == "ctrl u":
            try:
                self.set_focus(self.get_focus()[1] - 10)
            except IndexError:
                self.set_focus(0)
            self.reload_widget()
            return
        elif key == "G":
            self.set_focus(len(self.body) - 1)
            self.body[:] = self.body
            return
        elif key == "g":
            if self.cached_key is None:
                self.cached_key = "g"
            elif self.cached_key == "g":
                self.set_focus(0)
                self.reload_widget()
                self.cached_key = None
            return
        key = super().keypress(size, key)
        return key


class ScrollableListBox(VimMovementListBox):
    def __init__(self, text):
        # FIXME: put to utils, ensure it's unicode
        try:
            text = text.decode("utf-8")
        except AttributeError:
            pass
        list_of_texts = text.split("\n")
        self.walker = urwid.SimpleFocusListWalker([
            urwid.AttrMap(urwid.Text(t, align="left", wrap="any"), "main_list_dg", "main_list_white")
            for t in list_of_texts
        ])
        super().__init__(self.walker)


class AsyncScrollableListBox(VimMovementListBox):
    def __init__(self, generator, ui, static_data=None):
        self.log_texts = []
        if static_data:
            for d in static_data.decode("utf-8").split("\n"):
                log_entry = d.strip()
                if log_entry:
                    self.log_texts.append(urwid.Text(("main_list_dg", log_entry),
                                                     align="left", wrap="any"))
        walker = urwid.SimpleFocusListWalker(self.log_texts)
        super(AsyncScrollableListBox, self).__init__(walker)

        def fetch_logs():
            for line in generator:
                line = line.decode("utf-8")
                if self.stop.is_set():
                    break
                walker.append(
                    urwid.AttrMap(
                        urwid.Text(line.strip(), align="left", wrap="any"), "main_list_dg", "main_list_white"
                    )
                )
                walker.set_focus(len(walker) - 1)
                ui.refresh()

        self.stop = threading.Event()
        self.thread = threading.Thread(target=fetch_logs, daemon=True)
        self.thread.start()

    def destroy(self):
        self.stop.set()


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
        if focus_on_top:
            self.set_focus(0)

    def realtime_updates(self):
        """
        update listing realtime as events come from docker

        :return:
        """
        for content in self.d.realtime_updates():
            widgets = []
            for o in content:
                line = MainLineWidget(o)
                widgets.append(line)
            self.walker[:] = widgets
            self.ui.refresh()

    def _assemble_initial_content(self):
        widgets = []
        for o in self.d.initial_content():
            line = MainLineWidget(o)
            widgets.append(line)
        return widgets

    @property
    def focused_docker_object(self):
        return self.get_focus()[0].docker_object

    def _search(self, reverse_search=False):
        if self.search_string is None:
            raise NotifyError("No search pattern specified.")
        pos = self.focus_position
        while True:
            if reverse_search:
                obj, pos = self.body.get_prev(pos)
            else:
                obj, pos = self.body.get_next(pos)
            if obj is None:
                raise NotifyError("Pattern not found: %r." % self.search_string)
            if obj.matches_search(self.search_string):
                self.set_focus(pos)
                self.reload_widget()
                break

    def find_previous(self, search_pattern=None):
        if search_pattern is not None:
            self.search_string = search_pattern
        self._search(reverse_search=True)

    def find_next(self, search_pattern=None):
        if search_pattern is not None:
            self.search_string = search_pattern
        self._search()

    def keypress(self, size, key):
        # these functions will be executed in threads
        # provide arguments, don't access self.<attrib> b/c those will be
        # evaluated when the code is running, not when calling it
        def run_and_report_on_fail(fn_name, docker_object, notif_level="info"):
            try:
                operation = getattr(docker_object, fn_name)()
            except AttributeError:
                notif_txt = "You can't {} {} {!r}.".format(
                    fn_name,
                    docker_object.pretty_object_type.lower(),
                    docker_object.short_name)
                log_txt = "you can't {} {}".format(fn_name, docker_object)
                logger.error(log_txt)
                self.ui.notify(notif_txt, level="error")
            except Exception as ex:
                logger.error(repr(ex))
                self.ui.notify(str(ex), level="error")
            else:
                self.ui.notify(operation.pretty_message, level=notif_level)
                # we don't need to refresh whole buffer here, since we are getting realtime
                # updates using events call
                # self.ui.refresh_main_buffer()

        def do_and_report_on_fail(f, docker_object):
            try:
                f(docker_object)
            except NotifyError as ex:
                self.ui.notify(str(ex), level="error")
                logger.error(repr(ex))

        logger.debug("size %r, key %r", size, key)
        if key == "i":
            self.ui.run_in_background(do_and_report_on_fail, self.ui.inspect, self.focused_docker_object)
            return
        elif key == "l":
            self.ui.run_in_background(do_and_report_on_fail, self.ui.display_logs, self.focused_docker_object)
            return
        elif key == "f":
            self.ui.run_in_background(do_and_report_on_fail, self.ui.display_and_follow_logs, self.focused_docker_object)
            return
        elif key == "d":
            self.ui.run_in_background(run_and_report_on_fail, "remove", self.focused_docker_object,
                                      "error")
            return
        elif key == "s":
            self.ui.run_in_background(run_and_report_on_fail, "start", self.focused_docker_object)
            return
        elif key == "r":
            self.ui.run_in_background(run_and_report_on_fail, "restart", self.focused_docker_object)
            return
        elif key == "t":
            self.ui.run_in_background(run_and_report_on_fail, "stop", self.focused_docker_object)
            return
        elif key == "p":
            self.ui.run_in_background(run_and_report_on_fail, "pause", self.focused_docker_object)
            return
        elif key == "u":
            self.ui.run_in_background(run_and_report_on_fail, "unpause", self.focused_docker_object)
            return
        elif key == "X":
            self.ui.run_in_background(run_and_report_on_fail, "kill", self.focused_docker_object,
                                      "error")
            return

        key = super(MainListBox, self).keypress(size, key)
        return key
