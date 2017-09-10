"""
TODO:
 * nicer list
 * summary
 * clickable items
 * enable deleting volumes
"""
import urwid

from sen.util import humanize_bytes, graceful_chain_get
from sen.tui.views.base import View
from sen.tui.widgets.list.util import SingleTextRow
from sen.tui.widgets.table import assemble_rows
from sen.tui.constants import MAIN_LIST_FOCUS
from sen.tui.widgets.util import SelectableText, get_map
from sen.tui.widgets.list.base import WidgetBase


class DfBufferView(WidgetBase, View):
    def __init__(self, ui, buffer):
        """

        :param ui:
        :param buffer: Buffer instance, display help about this buffer
        """
        self.ui = ui
        self.buffer = buffer
        self.walker = urwid.SimpleFocusListWalker([])
        super().__init__(ui, self.walker)

    def refresh(self, df=None, containers=None, images=None):
        content = []
        if df is None:
            content += [
                SingleTextRow("Data is being loaded, it may even take a couple minutes.",
                              maps={"normal": "main_list_white", "focus": MAIN_LIST_FOCUS}),
            ]
        else:
            if containers:
                content += [
                    SingleTextRow("Containers",
                                  maps={"normal": "main_list_white", "focus": MAIN_LIST_FOCUS}),
                    SingleTextRow("")
                ]
                containers_content = [[
                    SelectableText("Name", maps=get_map("main_list_lg")),
                    SelectableText("Image Size", maps=get_map("main_list_lg")),
                    SelectableText("Writable Layer Size", maps=get_map("main_list_lg")),
                ]]
                for c in containers:
                    containers_content.append(
                        [SelectableText(c.short_name),
                         SelectableText(humanize_bytes(c.size_root_fs or 0)),
                         SelectableText(humanize_bytes(c.size_rw_fs or 0)),
                    ])
                content.extend(assemble_rows(containers_content, dividechars=3))
                content += [
                    SingleTextRow("")
                ]
            if images:
                content += [
                    SingleTextRow("Images",
                                  maps={"normal": "main_list_white", "focus": MAIN_LIST_FOCUS}),
                    SingleTextRow("")
                ]
                images_content = [[
                    SelectableText("Name", maps=get_map("main_list_lg")),
                    SelectableText("Size", maps=get_map("main_list_lg")),
                    SelectableText("Shared Size", maps=get_map("main_list_lg")),
                    SelectableText("Unique Size", maps=get_map("main_list_lg"))
                ]]
                for i in images:
                    images_content.append([
                        SelectableText(i.short_name, maps=get_map("main_list_dg")),
                        SelectableText(
                            humanize_bytes(i.total_size or 0),
                            maps=get_map("main_list_dg")),
                        SelectableText(
                            humanize_bytes(i.shared_size or 0),
                            maps=get_map("main_list_dg")),
                        SelectableText(
                            humanize_bytes(i.unique_size or 0),
                            maps=get_map("main_list_dg"))
                    ])
                content.extend(assemble_rows(images_content, dividechars=3))
                content += [
                    SingleTextRow("")
                ]
            volumes = graceful_chain_get(df, "Volumes")
            if volumes:
                content += [
                    SingleTextRow("Volumes",
                                  maps={"normal": "main_list_white", "focus": MAIN_LIST_FOCUS}),
                    SingleTextRow("")
                ]
                volumes_content = [[
                    SelectableText("Name", maps=get_map("main_list_lg")),
                    SelectableText("Links", maps=get_map("main_list_lg")),
                    SelectableText("Size", maps=get_map("main_list_lg")),
                ]]
                for v in volumes:
                    v_name = graceful_chain_get(v, "Name", default="")
                    v_size = graceful_chain_get(v, "UsageData", "Size", default=0)
                    v_links = graceful_chain_get(v, "UsageData", "RefCount", default=0)
                    volumes_content.append([
                        SelectableText(v_name, maps=get_map("main_list_dg")),
                        SelectableText("%s" % v_links, maps=get_map("main_list_dg")),
                        SelectableText(
                            humanize_bytes(v_size),
                            maps=get_map("main_list_dg")),
                    ])
                content.extend(assemble_rows(volumes_content, dividechars=3))
        self.set_body(content)
        self.set_focus(0)
