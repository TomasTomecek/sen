import urwid

from sen.tui.widgets.list.util import SingleTextRow
from sen.tui.widgets.table import assemble_rows
from . import View
from sen.tui.constants import MAIN_LIST_FOCUS
from sen.tui.widgets.util import SelectableText, get_map

from sen.tui.widgets.list.base import WidgetBase


class HelpView(WidgetBase, View):
    # TODO: on enter show description about the keybind/command
    def __init__(self, ui, buffer, global_keybinds):
        """

        :param ui:
        :param buffer: Buffer instance, display help about this buffer
        :param global_keybinds: dict
        """
        self.ui = ui
        self.buffer = buffer
        self.walker = urwid.SimpleFocusListWalker([])
        self.global_keybinds = global_keybinds
        super().__init__(ui, self.walker)

    def refresh(self):
        template = [
            SingleTextRow(self.buffer.display_name,
                          maps={"normal": "main_list_white", "focus": MAIN_LIST_FOCUS}),
            SingleTextRow(""),
            SingleTextRow(self.buffer.description,
                          maps={"normal": "main_list_dg", "focus": MAIN_LIST_FOCUS}),
            SingleTextRow(""),
            SingleTextRow("Global Keybindings",
                          maps={"normal": "main_list_white", "focus": MAIN_LIST_FOCUS}),
            SingleTextRow(""),
        ]

        template.extend(assemble_rows(
            [[SelectableText(key, maps=get_map("main_list_yellow")),
              SelectableText(command, maps=get_map("main_list_lg"))]
             for key, command in self.global_keybinds.items()],
            ignore_columns=[1], dividechars=3))
        if self.buffer.keybinds:
            template += [
                SingleTextRow(""),
                SingleTextRow("Buffer-specific Keybindings",
                              maps={"normal": "main_list_white", "focus": MAIN_LIST_FOCUS}),
                SingleTextRow(""),
            ]
            template.extend(assemble_rows(
                [[SelectableText(key, maps=get_map("main_list_yellow")),
                  SelectableText(command, maps=get_map("main_list_lg"))]
                 for key, command in self.buffer.keybinds.items()],
                ignore_columns=[1], dividechars=3))

        self.set_body(template)
        self.set_focus(0)
