import copy
import functools
import json
import logging
import datetime
import traceback

from sen.exceptions import TerminateApplication

import docker
import humanize


logger = logging.getLogger(__name__)


class ImageNameStruct(object):
    """
    stolen from atomic-reactor; thanks @mmilata!
    """
    def __init__(self, registry=None, namespace=None, repo=None, tag=None):
        self.registry = registry
        self.namespace = namespace
        self.repo = repo
        self.tag = tag

    @classmethod
    def parse(cls, image_name):
        result = cls()

        # registry.org/namespace/repo:tag
        s = image_name.split('/', 2)

        if len(s) == 2:
            if '.' in s[0] or ':' in s[0]:
                result.registry = s[0]
            else:
                result.namespace = s[0]
        elif len(s) == 3:
            result.registry = s[0]
            result.namespace = s[1]
        if result.namespace == 'library':
            # https://github.com/projectatomic/atomic-reactor/issues/45
            logger.debug("namespace 'library' -> ''")
            result.namespace = None
        result.repo = s[-1]

        try:
            result.repo, result.tag = result.repo.rsplit(':', 1)
        except ValueError:
            pass

        return result

    def to_str(self, registry=True, tag=True, explicit_tag=False,
               explicit_namespace=False):
        if self.repo is None:
            raise RuntimeError('No image repository specified')

        result = self.repo

        if tag and self.tag:
            result = '{0}:{1}'.format(result, self.tag)
        elif tag and explicit_tag:
            result = '{0}:{1}'.format(result, 'latest')

        if self.namespace:
            result = '{0}/{1}'.format(self.namespace, result)
        elif explicit_namespace:
            result = '{0}/{1}'.format('library', result)

        if registry and self.registry:
            result = '{0}/{1}'.format(self.registry, result)

        return result

    def __str__(self):
        return self.to_str(registry=True, tag=True)

    def __repr__(self):
        return "ImageName(image=%s)" % repr(self.to_str())

    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.to_str())

    def copy(self):
        return ImageNameStruct(
            registry=self.registry,
            namespace=self.namespace,
            repo=self.repo,
            tag=self.tag)


def operation(fmt_str):
    def wrap(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            command_took = None
            pretty_message = ""
            # cached queries do not access backend -- we don't care about that
            if kwargs.get("cached", False) is True:
                response = func(self, *args, **kwargs)
            else:
                before = datetime.datetime.now()
                response = func(self, *args, **kwargs)
                after = datetime.datetime.now()

                # we want milliseconds, not seconds
                command_took = (after - before).total_seconds() * 1000
                logger.debug("%s(%s, %s) %s -> [%f ms]", func.__name__, args, kwargs, self,
                             command_took)
            if fmt_str:
                pretty_message = fmt_str.format(object_type=getattr(self, "pretty_object_type", ""),
                                                object_short_name=getattr(self, "short_name", ""))
            return Operation(response, pretty_message=pretty_message, took=command_took)
        return wrapper
    return wrap


class Operation:
    """
    class for describing performed operation
    """

    def __init__(self, response, pretty_message="", took=None):
        self.response = response
        self.pretty_message = pretty_message
        self.took = took


class DockerObject:
    """
    Common base for images and containers
    """
    def __init__(self, data, docker_backend, object_id=None):
        self._id = object_id
        self._short_id = None
        self.data = data  # `client.containers` or `client.images`
        self.docker_backend = docker_backend
        self._created = None
        self._inspect = None
        self._names = None

    @property
    def d(self):
        """
        shortcut for instance of Docker client
        """
        return self.docker_backend.client

    @property
    def created(self):
        if self._created is None:
            self._created = datetime.datetime.fromtimestamp(self.data["Created"])
        return self._created

    def set_id(self):
        if self._id is None:
            try:
                self._id = self.data["Id"]
            except KeyError:
                raise RuntimeError("initial data not specified")

    @property
    def short_id(self):
        if self._short_id is None:
            self.set_id()
            self._short_id = self._id[:12]
        return self._short_id

    def display_time_created(self):
        return humanize.naturaltime(self.created)

    def inspect(self):
        raise NotImplementedError()

    def display_inspect(self):
        return json.dumps(self.inspect().response, indent=2)


def graceful_chain_get(d, *args):
    if not d:
        return None
    t = copy.deepcopy(d)
    for arg in args:
        try:
            t = t[arg]
        except (AttributeError, KeyError, TypeError):
            return None
    return t


class DockerImage(DockerObject):
    @property
    def image_id(self):
        if self._id is None:
            self.set_id()
        return self._id

    @property
    def parent_id(self):
        if self.data:
            return self.data.get("ParentId", None)
        else:
            inspect_operation = self.inspect(cached=True)
            return inspect_operation.response.get("Parent", None)

    @property
    def pretty_object_type(self):
        return "Image"

    @property
    def parent_image(self):
        try:
            parent_id = self.parent_id
        except Exception as ex:
            logger.error("error while getting parent ID of image %s: %r", self, ex)
            logger.info(traceback.format_exc())
            raise
        if parent_id:
            return DockerImage(None, self.docker_backend, object_id=parent_id)

    @property
    def command(self):
        cmd = graceful_chain_get(self.inspect(cached=True), "Config", "Cmd")
        if cmd:
            return " ".join(cmd)
        return ""

    @property
    def names(self):
        if self._names is None:
            self._names = []
            if self.data is None:
                return self._names
            for t in self.data["RepoTags"]:
                self._names.append(ImageNameStruct.parse(t))
            # sort by name length
            self._names.sort(key=lambda x: len(x.to_str()))
        return self._names

    @property
    def short_name(self):
        try:
            ins = self.names[0]
        except IndexError:
            return self.short_id
        if ins.repo == "<none>":
            return self.short_id
        return ins.to_str()

    def base_image(self):
        child_image = self
        while True:
            try:
                parent_image = self.docker_backend.get_image_by_id(child_image.parent_id)
            except Exception as ex:
                logger.warning("error while getting image by ID: %r", ex)
                parent_image = None
            if parent_image is None:
                try:
                    child_image = child_image.parent_image
                except Exception as ex:
                    logger.error("error while getting parent image for image %s: %r", self, ex)
                    return None
                if child_image is None:
                    return None
            else:
                return parent_image

    @operation("Inspect image {object_short_name}.")
    def inspect(self, cached=False):
        if self._inspect is None or cached is False:
            self._inspect = self.d.inspect_image(self.image_id)
        return self._inspect

    @operation("{object_type} {object_short_name} removed!")
    def remove(self):
        return self.d.remove_image(self.image_id)

    def matches_search(self, s):
        return s in self.image_id or \
            s in self.short_name

    def __str__(self):
        if self.names:
            return "{} ({}) {}".format(self.image_id, ", ".join([x.to_str() for x in self.names]), self.container_command)
        else:
            return "{} {}".format(self.image_id, self.container_command)

    def containers(self):
        return self.docker_backend.get_containers_for_image(self.image_id)


class DockerContainer(DockerObject):
    """
    Container related logic
    """

    def __str__(self):
        return "{} ({})".format(self.container_id, self.short_name)

    # properties

    @property
    def container_id(self):
        if self._id is None:
            self.set_id()
        return self._id

    @property
    def names(self):
        if self._names is None:
            self._names = []
            for t in self.data["Names"] or []:
                self._names.append(t)
            # sort by name length
            self._names.sort(key=lambda x: len(x))
        return self._names

    @property
    def command(self):
        return self.data["Command"]

    @property
    def status(self):
        return self.data["Status"]

    @property
    def running(self):
        return self.status.startswith("Up")

    @property
    def short_name(self):
        try:
            return self.names[0]
        except IndexError:
            return self.short_id

    @property
    def pretty_object_type(self):
        return "Container"

    @property
    def image_id(self):
        """ this container is created from image with id..."""
        image_id = self.data["ImageID"]
        return image_id

    # methods

    def image_name(self):
        image = self.docker_backend.get_image_by_id(self.image_id)
        if image is not None:
            return image.short_name
        else:
            return self.image_id[:12]

    def matches_search(self, s):
        return s in self.container_id or \
               s in self.short_name
    # api calls

    @operation("Inspect container {object_short_name}.")
    def inspect(self, cached=False):
        if cached is False or self._inspect is None:
            self._inspect = self.d.inspect_container(self.container_id)
        return self._inspect

    @operation("Logs of container {object_short_name} received.")
    def logs(self, follow=False):
        # when tail is set to all, it takes ages to populate widget
        logs_data = self.d.logs(self.container_id, stream=follow, tail=16)
        return logs_data

    @operation("{object_type} {object_short_name} removed!")
    def remove(self):
        self.d.remove_container(self.container_id)

    @operation("{object_type} {object_short_name} started.")
    def start(self):
        self.d.start(self.container_id)

    @operation("{object_type} {object_short_name} stopped.")
    def stop(self):
        self.d.stop(self.container_id)

    @operation("{object_type} {object_short_name} restarted.")
    def restart(self):
        self.d.restart(self.container_id)

    @operation("{object_type} {object_short_name} killed.")
    def kill(self):
        self.d.kill(self.container_id)

    @operation("{object_type} {object_short_name} paused.")
    def pause(self):
        self.d.pause(self.container_id)

    @operation("{object_type} {object_short_name} unpaused.")
    def unpause(self):
        self.d.unpause(self.container_id)


class DockerBackend:
    """
    backend for docker
    """

    def __init__(self):
        self._containers = None
        self._images = None
        kwargs = docker.utils.kwargs_from_env(assert_hostname=False)
        try:
            self.client = docker.AutoVersionClient(**kwargs)
        except docker.errors.DockerException as ex:
            raise TerminateApplication("can't establish connection to docker daemon: {0}".format(str(ex)))

    # backend queries

    @operation("Get list of images.")
    def get_images(self, cached=True):
        if cached is False or self._images is None:
            logger.debug("doing images() query")
            self._images = {}
            for i in self.client.images():
                img = DockerImage(i, self)
                self._images[img.image_id] = img
        return list(self._images.values())

    @operation("Get list of containers.")
    def get_containers(self, cached=True, stopped=True):
        if cached is False or self._containers is None:
            logger.debug("doing containers() query")
            self._containers = {}
            for c in self.client.containers(all=stopped):
                container = DockerContainer(c, self)
                self._containers[container.container_id] = container
        if not stopped:
            return [x for x in list(self._containers.values()) if x.running]
        return list(self._containers.values())

    def realtime_updates(self):
        for event in self.client.events(decode=True):
            logger.debug("RT event: %s", event)

            # event["from'] means it's a container
            if "from" in event:
                # inspect doesn't contain info about status and you can't query just one
                # container with containers()
                # let's do full-blown containers() query; it's not that expensive
                self.get_containers(cached=False)
            else:
                # similar as ^
                # images() doesn't support query by ID
                # inspect doesn't contain info about repositories
                self.get_images(cached=False)
            content, _, _ = self.filter(containers=True, images=True, stopped=True,
                                        cached=True, sort_by_created=True)
            yield content

    # service methods

    def get_image_by_id(self, image_id):
        return self._images.get(image_id)

    def get_container_by_id(self, container_id):
        return self._containers.get(container_id)

    def get_containers_for_image(self, image_id):
        return [container for container in self._containers.values() if container.image_id == image_id]

    def filter(self, containers=True, images=True, stopped=True, cached=False, sort_by_created=True):
        """
        since django is so awesome, let's use their ORM API

        :return:
        """
        content = []
        containers_o = None
        images_o = None
        # return containers when containers=False and running=True
        if containers or not stopped:
            containers_o = self.get_containers(cached=cached, stopped=stopped)
            content += containers_o.response
        if images:
            images_o = self.get_images(cached=cached)
            content += images_o.response
        if sort_by_created:
            content.sort(key=lambda x: x.created, reverse=True)
        return content, containers_o, images_o
