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


class DockerObject:
    """
    Common base for images and containers
    """
    def __init__(self, data):
        self.data = data

    @property
    def time_created(self):
        return self.data["Created"]

    def display_time_created(self):
        return humanize.naturaltime(datetime.datetime.fromtimestamp(self.data["Created"]))


class DockerImage(DockerObject):
    def __init__(self, data):
        super().__init__(data)
        self._inspect = None
        self._names = None

    @property
    def image_id(self):
        return self.data["Id"]

    @property
    def names(self):
        if self._names is None:
            self._names = []
            for t in self.data["RepoTags"]:
                self._names.append(ImageNameStruct.parse(t).to_str())
        return self._names


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

    def images(self, cached=True, sort="time"):
        if self._images is None or cached is False:
            self._images = []
            for i in self.client.images():
                self._images.append(DockerImage(i))
        if sort:
            if sort == "time":
                self._images.sort(key=lambda x: x.time_created, reverse=True)
        return self._images[:]

    def containers(self, cached=False, sort="time"):
        if self._containers is None or cached is False:
            self._containers = []
            for c in self.client.containers(all=True):
                self._containers.append(DockerContainer(c))
        if sort:
            if sort == "time":
                self._containers.sort(key=lambda x: x.time_created, reverse=True)
        return self._containers[:]

    def inspect_image(self, image_id):
        logger.debug("inspect image %r", image_id)
        inspect_data = self.client.inspect_image(image_id)
        logger.debug(inspect_data)
        return inspect_data

    def inspect_container(self, container_id):
        logger.debug("inspect container %r", container_id)
        inspect_data = self.client.inspect_container(container_id)
        logger.debug(inspect_data)
        return inspect_data

    def logs(self, container_id):
        logger.debug("get logs for container %r", container_id)
        logs_data = self.client.logs(container_id, stream=True)
        return logs_data

    def initial_content(self):
        content = self.images(sort=None) + self.containers(sort=None)
        content.sort(key=lambda x: x.time_created, reverse=True)
        return content
