import datetime
import json
import logging
import threading

import urwid

from sen.tui.constants import PALLETE, MAIN_LIST_FOCUS
from sen.docker_backend import DockerBackend, DockerImage, DockerContainer


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

            command = AdHocAttrMap(urwid.Text(o.command, wrap="clip"), get_map())
            self.widgets.append(command)
            columns.append(command)

            time = AdHocAttrMap(urwid.Text(o.display_time_created()), get_time_attr_map(o.created))
            self.widgets.append(time)
            columns.append((self.THIRD_COL, time))

            fourth = AdHocAttrMap(urwid.Text(" "), get_map())
            self.widgets.append(fourth)
            columns.append((self.FOURTH_COL, fourth))

            names_markup = []
            for n in o.names:
                logger.debug(n)
                if n.registry:
                    names_markup.append(("main_list_dg", n.registry + "/"))
                if n.namespace and n.repo:
                    names_markup.append(("main_list_lg", n.namespace + "/" + n.repo))
                else:
                    if n.repo == "<none>":
                        names_markup.append(("main_list_dg", n.repo))
                    else:
                        names_markup.append(("main_list_lg", n.repo))
                if n.tag:
                    if n.tag in ["<none>", "latest"]:
                        logger.debug("not displaying tag %r for image %s", n.tag, n)
                    else:
                        names_markup.append(("main_list_lg", ":" + n.tag))
                names_markup.append(("main_list_dg", ", "))
            names_markup = names_markup[:-1]
            names = AdHocAttrMap(urwid.Text(names_markup, wrap="clip"), get_map())
            self.widgets.append(names)
            columns.append(names)

            self.widgets = [image_id, names, time]

        elif isinstance(o, DockerContainer):
            container_id = AdHocAttrMap(urwid.Text(o.container_id[:12]), get_map())
            self.widgets.append(container_id)
            columns.append((12, container_id))

            command = AdHocAttrMap(urwid.Text(o.command, wrap="clip"), get_map())
            self.widgets.append(command)
            columns.append(command)

            time = AdHocAttrMap(urwid.Text(o.display_time_created()), get_time_attr_map(o.created))
            self.widgets.append(time)
            columns.append((self.THIRD_COL, time))

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

            name = AdHocAttrMap(urwid.Text(o.name, wrap="clip"), get_map())
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
    def __init__(self, static_data, generator, ui):
        self.log_texts = []
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
                logger.debug("log line emitted: %r", line)
                walker.append(urwid.Text(("text", line.strip()), align="left", wrap="any"))
                walker.set_focus(len(walker) - 1)
                ui.add_and_set_main_widget(self, True)

        self.stop = threading.Event()
        self.thread = threading.Thread(target=fetch_logs, daemon=True)
        self.thread.start()

    def destroy(self):
        self.stop.set()

class MainListBox(urwid.ListBox):
    def __init__(self, docker_backend, ui):
        self.d = docker_backend
        self.ui = ui
        self.widgets = self._assemble_initial_content()
        super(MainListBox, self).__init__(urwid.SimpleFocusListWalker(self.widgets))

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
        logger.debug("size %r, key %r", size, key)
        if key == "i":
            inspect_data = self.focused_docker_object.inspect()
            rendered_json = json.dumps(inspect_data, indent=2)
            self.ui.add_and_set_main_widget(ScrollableListBox(rendered_json))
            return
        elif key == "l":
            if isinstance(self.focused_docker_object, DockerContainer):
                logs_data, logs_generator = self.focused_docker_object.logs()
                w = AsyncScrollableListBox(logs_data, logs_generator, self.ui)
                self.ui.add_and_set_main_widget(w)
            return
        elif key == "d":
            self.focused_docker_object.remove()
            w = {}
            for o in self.d.initial_content():
                line = MainLineWidget(o)
                if isinstance(o, DockerContainer):
                    w[o.container_id] = line
                else:
                    w[o.image_id] = line
            for idx, row in enumerate(self.widgets):
                logger.debug(row)

                if isinstance(row.docker_object, DockerContainer):
                    try:
                        self.widgets[idx] = w[row.docker_object.container_id]
                    except KeyError:
                        del self.widgets[idx]
                else:
                    self.widgets[idx] = w[row.docker_object.image_id]
            return
        key = super(MainListBox, self).keypress(size, key)
        return key
