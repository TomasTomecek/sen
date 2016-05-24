"""
these commands may take long to finish, they are usually being run against external service (e.g.
docker engine)
"""
import logging

from sen.tui.buffer import LogsBuffer, InspectBuffer
from sen.tui.commands.base import BackendCommand, register_command, Argument
from sen.tui.widgets.list.util import get_operation_notify_widget


logger = logging.getLogger(__name__)


class OperationCommand(BackendCommand):
    def do(self, fn_name, pre_message=None, notif_level="info"):
        pre_message = pre_message or self.pre_info_message.format(
            container_name=self.docker_object.short_name)
        self.ui.notify_message(pre_message)
        try:
            operation = getattr(self.docker_object, fn_name)()
        except AttributeError:
            log_txt = "you can't {} {}".format(fn_name, self.docker_object)
            logger.error(log_txt)
            notif_txt = "You can't {} {} {!r}.".format(
                fn_name,
                self.docker_object.pretty_object_type.lower(),
                self.docker_object.short_name)
            self.ui.notify_message(notif_txt, level="error")
        except Exception as ex:
            self.ui.notify_message(str(ex), level="error")
            raise
        else:
            self.ui.remove_notification_message(pre_message)
            self.ui.notify_widget(
                get_operation_notify_widget(operation, notif_level=notif_level)
            )


class MatchingOperationCommand(OperationCommand):
    """ this is just a shortcut """
    def run(self):
        self.do(self.name)


@register_command
class RemoveCommand(OperationCommand):
    name = "rm"

    def run(self):
        self.do("remove",
                pre_message="Removing {} {}...".format(
                    self.docker_object.pretty_object_type.lower(),
                    self.docker_object.short_name),
                notif_level="important")


@register_command
class StartContainerCommand(MatchingOperationCommand):
    name = "start"
    pre_info_message = "Starting container {container_name}..."


@register_command
class StopContainerCommand(MatchingOperationCommand):
    name = "stop"
    pre_info_message = "Stopping container {container_name}..."


@register_command
class RestartContainerCommand(MatchingOperationCommand):
    name = "restart"
    pre_info_message = "Restarting container {container_name}..."


@register_command
class KillContainerCommand(MatchingOperationCommand):
    name = "kill"
    pre_info_message = "Killing container {container_name}..."


@register_command
class PauseContainerCommand(MatchingOperationCommand):
    name = "pause"
    pre_info_message = "Pausing container {container_name}..."


@register_command
class UnpauseContainerCommand(MatchingOperationCommand):
    name = "unpause"
    pre_info_message = "Unpausing container {container_name}..."


@register_command
class LogsCommand(BackendCommand):
    name = "logs"
    argument_definitions = [Argument("follow", "Follow logs.", default=False, aliases=["-f", "f"])]

    def run(self):
        self.ui.add_and_display_buffer(
            LogsBuffer(self.ui, self.docker_object, follow=self.arguments.follow))


@register_command
class InspectCommand(BackendCommand):
    name = "inspect"

    def run(self):
        if not self.docker_object:
            self.ui.notify_message("No docker object specified.", level="error")
            return
        self.ui.add_and_display_buffer(InspectBuffer(self.ui, self.docker_object))
