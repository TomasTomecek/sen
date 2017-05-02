import logging
import threading

import urwid
from sen.exceptions import NotifyError


logger = logging.getLogger(__name__)


class WidgetBase(urwid.ListBox):
    """
    common class for widgets
    """

    def __init__(self, ui, *args, **kwargs):
        self.ui = ui
        self.search_string = None
        self.filter_query = ""
        super().__init__(*args, **kwargs)
        self.ro_content = self.body[:]  # unfiltered content of a widget
        self.body_change_lock = threading.Lock()

    def set_body(self, widgets):
        with self.body_change_lock:
            self.body[:] = widgets

    def reload_widget(self):
        # this is the easiest way to refresh body
        with self.body_change_lock:
            self.body[:] = self.body

    def _search(self, reverse_search=False):
        if self.search_string is None:
            raise NotifyError("No search pattern specified.")
        if not self.search_string:
            self.search_string = None
            return
        pos = self.focus_position
        original_position = pos
        wrapped = False
        while True:
            if reverse_search:
                obj, pos = self.body.get_prev(pos)
            else:
                obj, pos = self.body.get_next(pos)
            if obj is None:
                # wrap
                wrapped = True
                if reverse_search:
                    obj, pos = self.body[-1], len(self.body)
                else:
                    obj, pos = self.body[0], 0
            if wrapped and (
                        (pos > original_position and not reverse_search) or
                        (pos < original_position and reverse_search)
            ):
                raise NotifyError("Pattern not found: %r." % self.search_string)
            # FIXME: figure out nicer search api
            if hasattr(obj, "matches_search"):
                condition = obj.matches_search(self.search_string)
            else:
                if hasattr(obj, "original_widget"):
                    text = obj.original_widget.text
                else:
                    text = obj.text
                condition = self.search_string in text
            if condition:
                self.set_focus(pos)
                self.reload_widget()
                break

    def filter(self, s, widgets_to_filter=None):
        s = s.strip()

        if not s:
            self.filter_query = None
            self.set_body(self.ro_content)
            return

        widgets = []
        for obj in widgets_to_filter or self.ro_content:

            # FIXME: figure out nicer search api
            if hasattr(obj, "matches_search"):
                condition = obj.matches_search(s)
            else:
                if hasattr(obj, "original_widget"):
                    text = obj.original_widget.text
                else:
                    text = obj.text
                condition = s in text

            if condition:
                widgets.append(obj)
        if not widgets_to_filter:
            self.filter_query = s
        self.set_body(widgets)

    def find_previous(self, search_pattern=None):
        if search_pattern is not None:
            self.search_string = search_pattern
        self._search(reverse_search=True)

    def find_next(self, search_pattern=None):
        if search_pattern is not None:
            self.search_string = search_pattern
        self._search()

    def status_bar(self):
        columns_list = []

        def add_subwidget(markup, color_attr=None):
            if color_attr is None:
                w = urwid.AttrMap(urwid.Text(markup), "status_text")
            else:
                w = urwid.AttrMap(urwid.Text(markup), color_attr)
            columns_list.append((len(markup), w))

        if self.search_string:
            add_subwidget("Search: ")
            add_subwidget(repr(self.search_string))

        if self.search_string and self.filter_query:
            add_subwidget(", ")

        if self.filter_query:
            add_subwidget("Filter: ")
            add_subwidget(repr(self.filter_query))

        return columns_list

    @property
    def focused_docker_object(self):
        return self.get_focus()[0].docker_object
