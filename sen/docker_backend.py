import copy
import json
import logging
import datetime
import _json

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


class DockerObject:
    """
    Common base for images and containers
    """
    def __init__(self, data, docker_client):
        self.data = data
        self.d = docker_client
        self._created = None

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
        except (AttributeError, KeyError):
            return None
    return t


class DockerImage(DockerObject):
    def __init__(self, data, docker_client):
        super().__init__(data, docker_client)
        self._inspect = None
        self._names = None

    @property
    def image_id(self):
        return self.data["Id"]

    @property
    def command(self):
        cmd = graceful_chain_get(self.data, "Config", "Cmd")
        if cmd:
            return " ".join(cmd)
        return ""

    @property
    def names(self):
        if self._names is None:
            self._names = []
            for t in self.data["RepoTags"]:
                self._names.append(ImageNameStruct.parse(t))
            # sort by name length
            self._names.sort(key=lambda x: len(x.to_str()))
        return self._names

    @property
    def short_name(self):
        return self.names[0]

    def inspect(self):
        logger.debug("inspect image %r", self.image_id)
        inspect_data = self.d.inspect_image(self.image_id)
        logger.debug(inspect_data)
        return inspect_data

    def remove(self):
        logger.debug("remove image %r", self.image_id)
        self.d.remove_image(self.image_id)

    def __str__(self):
        return "{} ({})".format(self.image_id, self.names)


class DockerContainer(DockerObject):
    @property
    def container_id(self):
        return self.data["Id"]

    @property
    def name(self):
        return self.data["Names"]

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
        return self.name

    def inspect(self):
        logger.debug("inspect container %r", self.container_id)
        inspect_data = self.d.inspect_container(self.container_id)
        logger.debug(inspect_data)
        return inspect_data

    def logs(self):
        logger.debug("get logs for container %r", self.container_id)
        logs_data = self.d.logs(self.container_id, stream=False)
        generator = self.d.logs(self.container_id, stream=True, tail=1)
        return logs_data, generator

    def remove(self):
        logger.debug("remove container %r", self.container_id)
        self.d.remove_container(self.container_id)

    def __str__(self):
        return "{} ({})".format(self.container_id, self.name)


class DockerBackend:
    """
    backend for docker
    """

    def __init__(self):
        self._client = None
        self._containers = None
        self._images = None

    @property
    def client(self):
        if self._client is None:
            self._client = docker.AutoVersionClient()
        return self._client

    def images(self, cached=True, sort_by_time=True):
        if self._images is None or cached is False:
            self._images = {}
            for i in self.client.images():
                img = DockerImage(i, self.client)
                self._images[img.image_id] = img
        if sort_by_time:
            v = list(self._images.values())
            v.sort(key=lambda x: x.time_created, reverse=True)
            return v
        return list(self._images.values())

    def containers(self, cached=False, sort_by_time=True, stopped=True):
        if self._containers is None or cached is False:
            self._containers = {}
            for c in self.client.containers(all=True):
                container = DockerContainer(c, self.client)
                self._containers[container.container_id] = container
        v = list(self._containers.values())
        if stopped is False:
            v = [x for x in v if x.running]
        if sort_by_time:
            v.sort(key=lambda x: x.time_created, reverse=True)
        return v

    def initial_content(self):
        content = self.images(sort_by_time=False) + self.containers(sort_by_time=False)
        content.sort(key=lambda x: x.created, reverse=True)
        return content
