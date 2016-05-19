import logging

from sen.tui.commands.base import register_command, SameThreadCommand


import urwidtrees


logger = logging.getLogger(__name__)


@register_command
class NavigateTopCommand(SameThreadCommand):
    name = "navigate-top"

    def run(self):
        # FIXME: refactor
        if isinstance(self.buffer.widget, urwidtrees.TreeBox):
            self.buffer.widget.focus_first()
        else:
            self.buffer.widget.set_focus(0)
            self.buffer.widget.reload_widget()


@register_command
class NavigateBottomCommand(SameThreadCommand):
    name = "navigate-bottom"

    def run(self):
        # FIXME: refactor
        if isinstance(self.buffer.widget, urwidtrees.TreeBox):
            self.buffer.widget.focus_last()
        else:
            self.buffer.widget.set_focus(len(self.buffer.widget.body) - 1)
            self.buffer.widget.reload_widget()


@register_command
class NavigateUpCommand(SameThreadCommand):
    name = "navigate-up"

    def run(self):
        return super(self.buffer.widget.__class__, self.buffer.widget).keypress(self.size, "up")


@register_command
class NavigateDownCommand(SameThreadCommand):
    name = "navigate-down"

    def run(self):
        return super(self.buffer.widget.__class__, self.buffer.widget).keypress(self.size, "down")


@register_command
class NavigateUpwardsCommand(SameThreadCommand):
    name = "navigate-upwards"

    def run(self):
        if isinstance(self.buffer.widget, urwidtrees.TreeBox):
            self.ui.notify_message("This movement is not available.", level="error")
            return
        try:
            self.buffer.widget.set_focus(self.buffer.widget.get_focus()[1] - 10)
        except IndexError:
            self.buffer.widget.set_focus(0)
        self.buffer.widget.reload_widget()
        return


@register_command
class NavigateDownwardsCommand(SameThreadCommand):
    name = "navigate-downwards"

    def run(self):
        if isinstance(self.buffer.widget, urwidtrees.TreeBox):
            self.ui.notify_message("This movement is not available.", level="error")
            return
        try:
            self.buffer.widget.set_focus(self.buffer.widget.get_focus()[1] + 10)
        except IndexError:
            self.buffer.widget.set_focus(len(self.buffer.widget.body) - 1)
        self.buffer.widget.reload_widget()
        return
