import urwid

from sen.tui.views.base import View
from sen.tui.widgets.list.util import SingleTextRow
from sen.tui.widgets.table import assemble_rows
from sen.tui.constants import MAIN_LIST_FOCUS
from sen.tui.widgets.util import SelectableText, get_map
from sen.tui.widgets.list.base import WidgetBase


class HelpBufferView(WidgetBase, View):
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
            SingleTextRow("Buffer: " + self.buffer.display_name,
                          maps={"normal": "main_list_white", "focus": MAIN_LIST_FOCUS}),
            SingleTextRow(""),
            SingleTextRow(self.buffer.description,
                          maps={"normal": "main_list_dg", "focus": MAIN_LIST_FOCUS}),
            SingleTextRow(""),
        ]

        if self.buffer.keybinds:
            template += [
                SingleTextRow("Buffer-specific Keybindings",
                              maps={"normal": "main_list_white", "focus": MAIN_LIST_FOCUS}),
                SingleTextRow(""),
            ]
            template.extend(assemble_rows(
                [[SelectableText(key, maps=get_map("main_list_yellow")),
                  SelectableText(command, maps=get_map("main_list_lg"))]
                 for key, command in self.buffer.keybinds.items()],
                ignore_columns=[1], dividechars=3))

        template += [
            SingleTextRow(""),
            SingleTextRow("Global Keybindings",
                          maps={"normal": "main_list_white", "focus": MAIN_LIST_FOCUS}),
            SingleTextRow("")
        ]
        template.extend(assemble_rows(
            [[SelectableText(key, maps=get_map("main_list_yellow")),
              SelectableText(command, maps=get_map("main_list_lg"))]
             for key, command in self.global_keybinds.items()],
            ignore_columns=[1], dividechars=3))

        self.set_body(template)
        self.set_focus(0)


class HelpCommandView(WidgetBase, View):
    def __init__(self, ui, command):
        """

        :param ui:
        :param command: Command instance
        """
        self.ui = ui
        self.command = command
        self.walker = urwid.SimpleFocusListWalker([])
        super().__init__(ui, self.walker)

    def refresh(self):
        invocation = ["[{}=value]".format(a.name) for a in self.command.options_definitions] + \
                     ["<{}>".format(o.name) for o in self.command.arguments_definitions]
        template = [
            SingleTextRow("Command: {} {}".format(self.command.name, " ".join(invocation)),
                          maps={"normal": "main_list_white", "focus": MAIN_LIST_FOCUS}),
            SingleTextRow(""),
        ]
        template += [SingleTextRow(s, maps={"normal": "main_list_dg", "focus": MAIN_LIST_FOCUS})
                     for s in self.command.description.split("\n")]
        template += [SingleTextRow("")]

        if self.command.arguments_definitions:
            template += [
                SingleTextRow(""),
                SingleTextRow("Arguments",
                              maps={"normal": "main_list_white", "focus": MAIN_LIST_FOCUS}),
                SingleTextRow(""),
            ]
            template.extend(assemble_rows(
                [[SelectableText(argument.name, maps=get_map("main_list_yellow")),
                  SelectableText(argument.description, maps=get_map("main_list_lg"))]
                 for argument in self.command.arguments_definitions],
                ignore_columns=[1], dividechars=3))

        if self.command.options_definitions:
            template += [
                SingleTextRow(""),
                SingleTextRow("Options",
                              maps={"normal": "main_list_white", "focus": MAIN_LIST_FOCUS}),
                SingleTextRow(""),
            ]
            template.extend(assemble_rows(
                [[SelectableText(option.name, maps=get_map("main_list_yellow")),
                  SelectableText(option.description, maps=get_map("main_list_lg"))]
                 for option in self.command.options_definitions],
                ignore_columns=[1], dividechars=3))

        self.set_body(template)
        self.set_focus(0)
