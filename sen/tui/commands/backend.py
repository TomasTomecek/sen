"""
these commands may take long to finish, they are usually being run against external service (e.g.
docker engine)
"""
import logging
import webbrowser

from sen.tui.buffer import LogsBuffer, InspectBuffer, DfBuffer
from sen.tui.commands.base import BackendCommand, register_command, Option
from sen.tui.widgets.list.util import get_operation_notify_widget
from sen.docker_backend import DockerContainer


logger = logging.getLogger(__name__)


class OperationCommand(BackendCommand):
    def do(self, fn_name, pre_message=None, notif_level="info", **kwargs):
        pre_message = pre_message or self.pre_info_message.format(
            container_name=self.docker_object.short_name)
        self.ui.notify_message(pre_message)
        try:
            operation = getattr(self.docker_object, fn_name)(**kwargs)
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
    description = "remove provided object, image or container"
    options_definitions = [Option("force",
                                  "Force removal of the selected object.",
                                  default=False, aliases=["-f", "f"]),
                           Option("yes",
                                  "Don't ask before removing.",
                                  default=False, aliases=["-y"])]

    def run(self):
        logger.debug("remove %s force=%s yes=%s", self.docker_object, self.arguments.force,
                     self.arguments.yes)
        if not self.arguments.yes and not self.ui.yolo:
            logger.debug("we need confirmation from user")
            cmd = "rm -y" if not self.arguments.force else "rm -y -f"
            self.ui.run_command(
                "prompt prompt-text=\"You are about to remove %s %s, type enter to continue: \" "
                "initial-text=\"%s\"" % (
                    self.docker_object.pretty_object_type.lower(),
                    self.docker_object.short_name,
                    cmd
                ),
                docker_object=self.docker_object
            )
            return

        if self.arguments.force:
            self.ui.notify_message("Removing forcibly!", level="important")
        self.do("remove",
                pre_message="Removing {} {}...".format(
                    self.docker_object.pretty_object_type.lower(),
                    self.docker_object.short_name),
                notif_level="important",
                force=self.arguments.force)


@register_command
class StartContainerCommand(MatchingOperationCommand):
    name = "start"
    description = "start a container"
    pre_info_message = "Starting container {container_name}..."


@register_command
class StopContainerCommand(MatchingOperationCommand):
    name = "stop"
    description = "stop a container"
    pre_info_message = "Stopping container {container_name}..."


@register_command
class RestartContainerCommand(MatchingOperationCommand):
    name = "restart"
    description = "restart a container"
    pre_info_message = "Restarting container {container_name}..."


@register_command
class KillContainerCommand(MatchingOperationCommand):
    name = "kill"
    description = "kill a container"
    pre_info_message = "Killing container {container_name}..."


@register_command
class PauseContainerCommand(MatchingOperationCommand):
    name = "pause"
    description = "pause a container"
    pre_info_message = "Pausing container {container_name}..."


@register_command
class UnpauseContainerCommand(MatchingOperationCommand):
    name = "unpause"
    description = "unpause a container"
    pre_info_message = "Unpausing container {container_name}..."


@register_command
class LogsCommand(BackendCommand):
    name = "logs"
    description = "display logs of a container"
    options_definitions = [Option("follow", "Follow logs.", default=False, aliases=["-f", "f"])]

    def run(self):
        self.ui.add_and_display_buffer(
            LogsBuffer(self.ui, self.docker_object, follow=self.arguments.follow))


@register_command
class InspectCommand(BackendCommand):
    name = "inspect"
    description = "inspect provided object, a container or an image"

    def run(self):
        if not self.docker_object:
            self.ui.notify_message("No docker object specified.", level="error")
            return
        self.ui.add_and_display_buffer(InspectBuffer(self.ui, self.docker_object))


@register_command
class DfCommand(BackendCommand):
    name = "df"
    description = "show disk usage"

    def run(self):
        b = DfBuffer(self.ui)
        self.ui.add_and_display_buffer(b)
        df = self.docker_backend.df()
        b.refresh(df=df.response,
                  containers=self.docker_backend.get_containers(cached=True, stopped=True).response,
                  images=self.docker_backend.get_images(cached=True).response)


@register_command
class OpenPortsInBrowser(BackendCommand):
    name = "open-browser"
    # TODO: user should be able to specify port and ip: by hitting keybind in container info view
    description = "open exposed port in a browser"

    def run(self):
        if not isinstance(self.docker_object, DockerContainer):
            self.ui.notify_message("No docker container specified.", level="error")
            return

        if not self.docker_object.running:
            self.ui.notify_message("Container is not running - no ports are available.",
                                   level="error")
            return

        ports = list(self.docker_object.net.ports.keys())
        ips = self.docker_object.net.ips

        logger.debug("ports = %s, ips = %s", ports, ips)

        if not ports:
            self.ui.notify_message(
                "Container %r doesn't expose any ports." % self.docker_object.short_name,
                level="error"
            )
            return

        url = "http://{}:{}".format(ips[list(ips.keys())[0]]["ip_address4"], ports[0])
        logger.info("opening %s in browser", url)
        webbrowser.open(url)
