import functools
import json
import logging
import datetime
import traceback
from operator import attrgetter

from sen.constants import ISO_DATETIME_PARSE_STRING
from sen.exceptions import (
    TerminateApplication, NotifyError, NotAvailableAnymore
)

import docker
import docker.errors

from sen.net import NetData
from sen.util import (
    calculate_cpu_percent, calculate_cpu_percent2, calculate_blkio_bytes,
    calculate_network_bytes, repeater,
    humanize_time,
    graceful_chain_get
)

logger = logging.getLogger(__name__)


DINOSAUR_TIME = datetime.datetime.fromordinal(1)


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

        result = self.repo if self.repo != "<none>" else ""

        # don't display <none> junk
        if tag and self.tag and self.tag != "<none>":
            result = '{0}:{1}'.format(result, self.tag)
        elif tag and explicit_tag and self.tag != "<none>":
            result = '{0}:{1}'.format(result, 'latest')

        # don't display <none> junk
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
            pretty_message = ""

            before = datetime.datetime.now()
            response = func(self, *args, **kwargs)
            after = datetime.datetime.now()

            # we want milliseconds, not seconds
            command_took = (after - before).total_seconds() * 1000
            # # this line literally break zsh; wat?
            # logger.debug("%s(%s, %s) %s -> [%f ms]", func.__name__, args, kwargs, self,
            #              command_took)
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
    def created_int(self):
        return self.data["Created"]

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
    def object_id(self):
        if self._id is None:
            self.set_id()
        return self._id

    @property
    def short_id(self):
        if self._short_id is None:
            self.set_id()
            if ":" in self._id:
                colon_index = self._id.index(":") + 1
                self._short_id = self._id[colon_index:][:12]
            else:
                self._short_id = self._id[:12]
        return self._short_id

    def display_time_created(self):
        return humanize_time(self.created)

    def display_formal_time_created(self):
        # http://tools.ietf.org/html/rfc2822.html#section-3.3
        return self.created.strftime("%d %b %Y, %H:%M:%S")

    def inspect(self, cached=True):
        raise NotImplementedError()

    def display_inspect(self):
        try:
            return json.dumps(self.inspect().response, indent=2)
        except docker.errors.NotFound:
            raise NotAvailableAnymore()

    @property
    def labels(self):
        labels = self.data["Labels"]
        return labels

    @property
    def natural_sort_value(self):
        return self.created

    def metadata_get(self, path, cached=True):
        """
        get metadata from inspect, specified by path

        :param path: list of str
        :param cached: bool, use cached version of inspect if available
        """
        try:
            value = graceful_chain_get(self.inspect(cached=cached).response, *path)
        except docker.errors.NotFound:
            logger.warning("object %s is not available anymore", self)
            raise NotAvailableAnymore()
        return value

    def refresh(self):
        """ refresh metadata """
        self.inspect(cached=False)

    def __eq__(self, other):
        return type(self) == type(other) and self._id == other._id

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self._id)


class DockerImage(DockerObject):
    def __init__(self, data, docker_backend, object_id=None):
        super().__init__(data, docker_backend, object_id=object_id)
        self._unique_size = None
        self._total_size = None
        self._virtual_size = None
        self._shared_size = None

    @property
    def image_id(self):
        return self.object_id

    @property
    def parent_id(self):
        if self.data:
            return self.data.get("ParentId", None)
        else:
            return self.metadata_get(["Parent"])

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
            return self.docker_backend.get_image_by_id(parent_id)
        else:
            return self.docker_backend.scratch_image

    @property
    def layers(self):
        """
        similar as parent images, except that it uses /history API endpoint
        :return:
        """
        # sample output:
        # {
        #     "Created": 1457116802,
        #     "Id": "sha256:507cb13a216097710f0d234668bf64a4c92949c573ba15eba13d05aad392fe04",
        #     "Size": 204692029,
        #     "Tags": [
        #         "docker.io/fedora:latest"
        #     ],
        #     "Comment": "",
        #     "CreatedBy": "/bin/sh -c #(nop) ADD file:bcb5e5c... in /"
        # }
        try:
            response = self.d.history(self.image_id)
        except docker.errors.NotFound:
            raise NotAvailableAnymore()

        layers = []
        for l in response:
            layer_id = l["Id"]
            if layer_id == "<missing>":
                layers.append(DockerImage(l, self.docker_backend))
            else:
                layers.append(self.docker_backend.get_image_by_id(layer_id))
        return layers

    @property
    def children(self):
        return self.docker_backend.get_images_for_parent(self)

    def get_next_sibling(self):
        imgs = self.parent_image.children
        if len(imgs) == 1:
            return None
        try:
            return imgs[imgs.index(self) + 1]
        except IndexError:
            return None

    def get_prev_sibling(self):
        imgs = self.parent_image.children
        if len(imgs) == 1:
            return None
        # 0 - 1 turns into -1 which turns into last element which creates cycle
        # which totally messes up whole tree
        prev_index = imgs.index(self) - 1
        if prev_index < 0:
            return None
        else:
            return imgs[prev_index]

    @property
    def command(self):
        cmd = self.metadata_get(["Config", "Cmd"])
        if cmd:
            return " ".join(cmd)
        return ""

    @property
    def container_command(self):
        # history item
        created_by = graceful_chain_get(self.data, "CreatedBy")
        if created_by:
            return created_by
        try:
            cmd = self.metadata_get(["ContainerConfig", "Cmd"])
        except NotAvailableAnymore:
            pass
        else:
            if cmd:
                return " ".join(cmd)
        return ""

    @property
    def comment(self):
        return self.metadata_get(["Comment"])

    @property
    def total_size(self):
        """
        Size of ALL layers in bytes

        :return: int or None
        """
        return self._total_size or self.data.get("Size", 0)

    @property
    def unique_size(self):
        """
        Size of ONLY this particular layer

        :return: int or None
        """
        self._virtual_size = self._virtual_size or \
                             graceful_chain_get(self.data, "VirtualSize", default=0)
        try:
            return self._virtual_size - self._shared_size
        except TypeError:
            return 0

    @property
    def shared_size(self):
        """
        I guess this is size of layers which are shared with some other image

        :return: int or None
        """
        return self._shared_size

    @property
    def names(self):
        if self._names is None:
            self._names = []
            if self.data is None:
                return self._names
            # RepoTags = image, Tags = output from `history` command, Tags can be None
            for t in self.data.get("RepoTags", self.data.get("Tags")) or []:
                image_name = ImageNameStruct.parse(t)
                if image_name.to_str():
                    self._names.append(image_name)
            # RepoDigests can be none
            for t in self.data.get("RepoDigests", []) or []:
                image_name = ImageNameStruct.parse(t)
                if image_name.to_str():
                    self._names.append(image_name)
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
            try:
                self._inspect = self.d.inspect_image(self.image_id)
            except docker.errors.NotFound:
                self._inspect = self._inspect or {}
        return self._inspect

    @operation("{object_type} {object_short_name} removed!")
    def remove(self, force=False):
        return self.d.remove_image(self.image_id, force=force)

    @operation("Tag of {object_type} {object_short_name} removed!")
    def remove_tag(self, tag):
        assert tag in self.names
        return self.d.remove_image(str(tag))

    def matches_search(self, s):
        return s in self.image_id or any([s in str(x) for x in self.names])

    def __str__(self):
        # it's dangerous to put many stuff here b/c most of the values are loaded dynamically
        # and it's trivial to go into nested exception madness
        return "image {}".format(self.short_id)

    def __repr__(self):
        return self.__str__()

    def containers(self):
        return self.docker_backend.get_containers_for_image(self.image_id)


class RootImage(DockerImage):
    """
    this is essentially "scratch" but you cannot inspect it anymore
    """
    def __init__(self, docker_backend):
        self.image_name = "scratch"
        super().__init__(None, docker_backend, object_id="")

    @property
    def parent_id(self):
        return None

    @property
    def parent_image(self):
        return None

    def get_next_sibling(self):
        return None

    def get_prev_sibling(self):
        return None

    @property
    def names(self):
        return [ImageNameStruct.parse(self.image_name)]

    def __str__(self):
        return self.image_name


class DockerContainer(DockerObject):
    """
    Container related logic
    """

    def __init__(self, data, docker_backend, object_id=None):
        super(DockerContainer, self).__init__(data, docker_backend, object_id)
        self.size_root_fs = None
        self.size_rw_fs = None

    def __str__(self):
        return "{} ({})".format(self.container_id, self.short_name)

    # properties

    @property
    def container_id(self):
        return self.object_id

    @property
    def names(self):
        if self._names is None:
            self._names = []
            for t in self.data.get("Names", []):
                self._names.append(t)
            # sort by name length
            self._names.sort(key=lambda x: len(x))
        return self._names

    @property
    def command(self):
        return self.data["Command"]

    @property
    def nice_status(self):
        return self.data["Status"]

    @property
    def simple_status(self):
        return self.metadata_get(["State", "Status"])

    @property
    def simple_status_cap(self):
        return self.simple_status.capitalize()

    @property
    def running(self):
        return self.metadata_get(["State", "Running"])

    @property
    def status_created(self):
        return self.simple_status == "created"

    @property
    def exit_code(self):
        return self.metadata_get(["State", "ExitCode"])

    @property
    def exited_well(self):
        return self.exit_code == 0

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
        try:
            # docker >= 1.9
            image_id = self.data["ImageID"]
        except KeyError:
            # docker <= 1.8
            image_id = self.metadata_get(["Image"])
        return image_id

    @property
    def image(self):
        return self.docker_backend.get_image_by_id(self.image_id)

    @property
    def ip_address(self):
        # docker == 1.10
        ip_address = self.metadata_get(["NetworkSettings", "IPAddress"])
        return ip_address

    @property
    def net(self):
        """
        get ACTIVE port mappings of a container

        :return: dict:
        {
            "host_port": "container_port"
        }
        """
        try:
            return NetData(self.inspect(cached=True).response)
        except docker.errors.NotFound:
            raise NotAvailableAnymore()

    @property
    def started_at(self):
        s = self.metadata_get(["State", "StartedAt"])
        if s:
            # python expects 6 digits in milliseconds, docker returns 9
            s = s[:26]
            if s == "0001-01-01T00:00:00Z":
                return DINOSAUR_TIME
            s = s.replace("Z", "0")
            try:
                started_at = datetime.datetime.strptime(s, ISO_DATETIME_PARSE_STRING)
            except ValueError as ex:
                logger.error("unable to parse datetime %s: %s", s, ex)
                return DINOSAUR_TIME
            return started_at

    @property
    def finished_at(self):
        f = self.metadata_get(["State", "FinishedAt"])
        if f:
            f = f[:26]
            if f == "0001-01-01T00:00:00Z":
                return DINOSAUR_TIME
            finished_at = datetime.datetime.strptime(f, ISO_DATETIME_PARSE_STRING)
            return finished_at

    @property
    def natural_sort_value(self):
        # docker acts weird: 'created' is provided as ordinal and is local time
        # 'started' and 'finished' are UTC as timestamp; it would be awesome to unite those b/c
        # atm these inconsistencies mess ordering
        try:
            # Nones are unsortable
            return max([x for x in
                        [self.started_at, self.finished_at, super().natural_sort_value]
                        if x])
        except NotAvailableAnymore:
            return super().natural_sort_value

    # methods

    def image_name(self):
        if self.image is not None:
            return self.image.short_name
        else:
            return self.image_id[:12]

    def matches_search(self, s):
        return s in self.container_id or \
               s in self.short_name
    # api calls

    @operation("Get resources statistics.")
    def stats(self):
        cpu_total = 0.0
        cpu_system = 0.0
        cpu_percent = 0.0
        for x in self.d.stats(self.container_id, decode=True, stream=True):
            blk_read, blk_write = calculate_blkio_bytes(x)
            net_r, net_w = calculate_network_bytes(x)
            mem_current = x["memory_stats"]["usage"]
            mem_total = x["memory_stats"]["limit"]

            try:
                cpu_percent, cpu_system, cpu_total = calculate_cpu_percent2(x, cpu_total, cpu_system)
            except KeyError as e:
                logger.error("error while getting new CPU stats: %r, falling back")
                cpu_percent = calculate_cpu_percent(x)

            r = {
                "cpu_percent": cpu_percent,
                "mem_current": mem_current,
                "mem_total": x["memory_stats"]["limit"],
                "mem_percent": (mem_current / mem_total) * 100.0,
                "blk_read": blk_read,
                "blk_write": blk_write,
                "net_rx": net_r,
                "net_tx": net_w,
            }
            yield r

    @operation("List processes in running container.")
    def top(self):
        """
        list of processes in a running container

        :return: None or list of dicts
        """
        # let's get resources from .stats()
        ps_args = "-eo pid,ppid,wchan,args"
        # returns {"Processes": [values], "Titles": [values]}
        # it's easier to play with list of dicts: [{"pid": 1, "ppid": 0}]
        try:
            response = self.d.top(self.container_id, ps_args=ps_args)
        except docker.errors.APIError as ex:
            logger.warning("error getting processes: %r", ex)
            return []
        # TODO: sort?
        logger.debug(json.dumps(response, indent=2))
        return [dict(zip(response["Titles"], process))
                for process in response["Processes"] or []]

    @operation("Inspect container {object_short_name}.")
    def inspect(self, cached=False):
        if cached is False or self._inspect is None:
            try:
                self._inspect = self.d.inspect_container(self.container_id)
            except docker.errors.NotFound:
                self._inspect = self._inspect or {}
        return self._inspect

    @operation("Logs of container {object_short_name} received.")
    def logs(self, follow=False, lines="all"):
        # when tail is set to all, it takes ages to populate widget
        # docker-py does `inspect` in the background
        try:
            logs_data = self.d.logs(self.container_id, stream=follow, tail=lines)
        except docker.errors.NotFound:
            return None
        else:
            return logs_data

    @operation("{object_type} {object_short_name} removed!")
    def remove(self, force=False):
        self.d.remove_container(self.container_id, force=force)

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
        self._images = None  # displayed images
        self._all_images = None  # docker images -a
        self._df = None

        kwargs = {"version": "auto"}
        kwargs.update(docker.utils.kwargs_from_env(assert_hostname=False))

        try:
            APIClientClass = docker.Client  # 1.x
        except AttributeError:
            APIClientClass = docker.APIClient  # 2.x

        try:
            self.client = APIClientClass(**kwargs)
        except docker.errors.DockerException as ex:
            raise TerminateApplication("can't establish connection to docker daemon: {0}".format(str(ex)))

        self.scratch_image = RootImage(self)

    # backend queries

    @operation("Get list of images.")
    def get_images(self, cached=True):
        if cached is False or self._images is None:
            logger.debug("doing images() query")
            self._images = {}
            images_response = repeater(self.client.images) or []
            for i in images_response:
                img = DockerImage(i, self)
                self._images[img.image_id] = img
            self._all_images = {}
            # FIXME: performance: do just all=True
            all_images_response = repeater(self.client.images, kwargs={"all": True}) or []
            for i in all_images_response:
                img = DockerImage(i, self)
                self._all_images[img.image_id] = img
        return list(self._images.values())

    @operation("Get list of containers.")
    def get_containers(self, cached=True, stopped=True):
        if cached is False or self._containers is None:
            logger.debug("doing containers() query")
            self._containers = {}
            containers_reponse = repeater(self.client.containers, kwargs={"all": stopped}) or []
            for c in containers_reponse:
                container = DockerContainer(c, self)
                self._containers[container.container_id] = container
        if not stopped:
            return [x for x in list(self._containers.values()) if x.running]
        return list(self._containers.values())

    @operation("Get disk usage.")
    def df(self, cached=True):
        if cached is False or self._df is None:
            logger.debug("getting disk-usage")
            # TODO: wrap in try/execpt
            self._df = self.client.df()
            # TODO: attach these to real containers and images
            # # since DOCKER API-1.25 (v.1.13.0)
            # df = self.client.df()
            # if 'Containers' in df:
            #     df_containers = df['Containers']
            containers_data = graceful_chain_get(self._df, "Containers")
            for c_data in containers_data:
                c = graceful_chain_get(self._containers, graceful_chain_get(c_data, "Id"))
                c.size_root_fs = graceful_chain_get(c_data, "SizeRootFs")
                c.size_rw_fs = graceful_chain_get(c_data, "SizeRw")
            images_data = graceful_chain_get(self._df, "Images")
            for i_data in images_data:
                i = graceful_chain_get(self._images, graceful_chain_get(i_data, "Id"))
                i._total_size = graceful_chain_get(i_data, "Size")
                i._shared_size = graceful_chain_get(i_data, "SharedSize")
                i._virtual_size = graceful_chain_get(i_data, "VirtualSize")
        return self._df

    def realtime_updates(self):
        event = it = None
        while True:
            if not it or not event:
                it = repeater(self.client.events, kwargs={"decode": True}, retries=5)
                if not it:
                    raise NotifyError("Unable to fetch realtime updates from docker engine.")

            event = repeater(next, args=(it, ), retries=2)  # likely an engine restart
            if not event:
                continue

            logger.debug("RT event: %s", event)

            yield event

            # try:
            #     # 1.10+
            #     is_container = event["Type"] == "container"
            # except KeyError:
            #     # event["from'] means it's a container
            #     is_container = "from" in event
            # if is_container:
            #     # inspect doesn't contain info about status and you can't query just one
            #     # container with containers()
            #     # let's do full-blown containers() query; it's not that expensive
            #     self.get_containers(cached=False)
            # else:
            #     # similar as ^
            #     # images() doesn't support query by ID
            #     # inspect doesn't contain info about repositories
            #     self.get_images(cached=False)
            # content, _, _ = self.filter(containers=True, images=True, stopped=True,
            #                             cached=True, sort_by_created=True)
            # yield content

    # service methods

    def get_image_by_id(self, image_id):
        return self._all_images.get(image_id)

    def get_images_for_parent(self, image):
        if not image:
            return []
        l = sorted([x for x in self._all_images.values() if x.parent_image == image], key=lambda x: x.created_int)
        return l

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
            content.sort(key=attrgetter("natural_sort_value"), reverse=True)
        return content, containers_o, images_o
