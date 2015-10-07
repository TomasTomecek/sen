import copy
import functools
import json
import logging
import datetime

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


def response_time(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # cached queries do not access backend -- we don't care about that
        if kwargs.get("cached", False) is True:
            return func(self, *args, **kwargs)
        before = datetime.datetime.now()
        response = func(self, *args, **kwargs)
        after = datetime.datetime.now()
        if isinstance(self, DockerBackend):
            b = self
        elif isinstance(self, DockerObject):
            b = self.docker_backend
        else:
            raise RuntimeError("wrong instance")
        b.last_command = func.__name__
        # we want milliseconds, not seconds
        b.last_command_took = (after - before).total_seconds() * 1000
        logger.debug("%s(%s, %s) -> [%f ms]", b.last_command, args, kwargs, b.last_command_took)
        return response
    return wrapper


class DockerObject:
    """
    Common base for images and containers
    """
    def __init__(self, data, docker_backend, object_id=None):
        self._id = object_id
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

    def display_time_created(self):
        return humanize.naturaltime(self.created)

    def inspect(self):
        raise NotImplementedError()

    def display_inspect(self):
        return json.dumps(self.inspect(), indent=2)


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
            try:
                self._id = self.data["Id"]
            except KeyError:
                raise RuntimeError("initial data not specified")
        return self._id

    @property
    def parent_id(self):
        if self.data:
            return self.data.get("ParentId", None)
        else:
            return self.inspect(cached=True).get("Parent", None)

    @property
    def parent_image(self):
        parent_id = self.parent_id
        if parent_id:
            return DockerImage(None, self.docker_backend, object_id=parent_id)
        raise RuntimeError("{} has no parent".format(self))

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
            return self.names[0]
        except IndexError:
            return self.image_id[:12]

    def base_image(self):
        child_image = self
        while True:
            parent_image = self.docker_backend.get_image_by_id(child_image.parent_id)
            if parent_image is None:
                try:
                    child_image = child_image.parent_image
                except RuntimeError:
                    logger.info("no base image for %s", self)
                    return None
            else:
                return parent_image

    @response_time
    def inspect(self, cached=False):
        if cached is False or self._inspect is None:
            self._inspect = self.d.inspect_image(self.image_id)
        return self._inspect

    @response_time
    def remove(self):
        self.d.remove_image(self.image_id)

    def __str__(self):
        return "{} ({})".format(self.image_id, self.names)


class DockerContainer(DockerObject):
    @property
    def container_id(self):
        return self.data["Id"]

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
            return self.container_id[:12]

    def image_name(self):
        image_name = self.data["Image"]
        image = self.docker_backend.get_image_by_id(image_name)
        if image is not None:
            return image.short_name.to_str()
        else:
            return image_name[:12]

    @response_time
    def inspect(self, cached=False):
        if cached is False or self._inspect is None:
            self._inspect = self.d.inspect_container(self.container_id)
        return self._inspect

    @response_time
    def logs(self):
        logs_data = self.d.logs(self.container_id, stream=False)
        generator = self.d.logs(self.container_id, stream=True, tail=1)
        return logs_data, generator

    def remove(self):
        self.d.remove_container(self.container_id)

    def start(self):
        self.d.start(self.container_id)

    def stop(self):
        self.d.stop(self.container_id)

    def restart(self):
        self.d.restart(self.container_id)

    def kill(self):
        self.d.kill(self.container_id)

    def pause(self):
        self.d.pause(self.container_id)

    def unpause(self):
        self.d.unpause(self.container_id)

    def __str__(self):
        return "{} ({})".format(self.container_id, self.short_name)


class DockerBackend:
    """
    backend for docker
    """

    def __init__(self):
        self._client = None
        self._containers = None
        self._images = None
        self.last_command = ""
        self.last_command_took = None  # milliseconds

    # lazy properties

    @property
    def client(self):
        if self._client is None:
            self._client = docker.AutoVersionClient()
        return self._client

    @property
    def images(self):
        if self._images is None:
            self.get_images()
        return self._images

    @property
    def containers(self):
        if self._containers is None:
            self.get_containers()
        return self._containers

    # backend queries

    @response_time
    def get_images(self, return_list=True):
        logger.debug("doing images() query")
        self._images = {}
        for i in self.client.images():
            img = DockerImage(i, self)
            self._images[img.image_id] = img
        if return_list:
            return list(self._images.values())
        else:
            return self._images

    def sorted_images(self, sort_by_time=False):
        v = list(self.images.values())
        if sort_by_time:
            v.sort(key=lambda x: x.time_created, reverse=True)
        return v

    @response_time
    def get_containers(self, return_list=True):
        logger.debug("doing containers() query")
        self._containers = {}
        for c in self.client.containers(all=True):
            container = DockerContainer(c, self)
            self._containers[container.container_id] = container
        if return_list:
            return list(self._containers.values())
        else:
            return self._containers

    def sorted_containers(self, sort_by_time=False, stopped=True):
        v = list(self.containers.values())
        if stopped is False:
            v = [x for x in v if x.running]
        if sort_by_time:
            v.sort(key=lambda x: x.time_created, reverse=True)
        return v

    # service methods

    def get_image_by_id(self, image_id):
        return self._images.get(image_id, None)

    def initial_content(self):
        content = self.get_containers() + self.get_images()
        content.sort(key=lambda x: x.created, reverse=True)
        return content
