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
            logging.debug("namespace 'library' -> ''")
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


class DockerImage():
    def __init__(self, data):
        self.data = data
        self._inspect = None
        self._names = None

    @property
    def image_id(self):
        return self.data["Id"]

    @property
    def time_created(self):
        return self.data["Created"]

    def display_time_created(self):
        return humanize.naturaltime(datetime.datetime.fromtimestamp(self.data["Created"]))

    @property
    def names(self):
        if self._names is None:
            self._names = []
            for t in self.data["RepoTags"]:
                self._names.append(ImageNameStruct.parse(t).to_str())
        return self._names


class DockerContainer():
    def __init__(self, data):
        self.data = data


class DockerBackend():
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
        return self._images

    def inspect_image(self, image_id):
        logging.debug("inspect image %r", image_id)
        inspect_data = self.client.inspect_image(image_id)
        logging.debug(inspect_data)
        return inspect_data
