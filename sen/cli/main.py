#!/usr/bin/python3
"""
yes, this is python 3 ONLY project
"""
import json
import sys
import logging
import datetime

import urwid
import docker
import humanize


logging.basicConfig(filename='debug.log', level=logging.DEBUG)


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
        return ImageName(
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


def exit_on_q(key):
    logging.debug("got %r", key)
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()

def image_clicked(*args):
    pass


class DockerImageColumns(urwid.Columns):

    def __init__(self, image_id, widgets):
        self.image_id = image_id
        super(DockerImageColumns, self).__init__(widgets)

    def selectable(self):
        return True

    def keypress(self, size, key):
        return key

    def get_image_id(self):
        return self.image_id


class DockerImagesListBox(urwid.ListBox):
    def __init__(self, ui):
        body = []
        self.d = DockerBackend()
        self.ui = ui
        for i in self.d.images():
            # # wrap
            # clip - cut overflow
            # any - overflow
            # space - overflow
            image_id = urwid.Text(("image_id", i.image_id[:12]), align="left", wrap="any")
            time = urwid.Text(("image_id", i.display_time_created()), align="left", wrap="any")
            names = urwid.Text(("image_names", i.names or ""), align="left", wrap="clip")
            line = DockerImageColumns(i.image_id, [image_id, names, time])
            body.append(urwid.AttrMap(line, 'image_id', focus_map='reversed'))
        body = urwid.SimpleFocusListWalker(body)
        super(DockerImagesListBox, self).__init__(body)

    def keypress(self, size, key):
        logging.debug("size %r, key %r", size, key)
        # import ipdb ; ipdb.set_trace()
        if key == "i":
            columns_widget = self.get_focus()[0].original_widget
            inspect_data = self.d.inspect_image(columns_widget.get_image_id())

            self.ui.top_widget.original_widget = urwid.Filler(urwid.Text(json.dumps(inspect_data, indent=2)))
            return
        key = super(DockerImagesListBox, self).keypress(size, key)
        return key

class UI():
    def __init__(self):
        self.top_widget = urwid.Padding(DockerImagesListBox(self))
        body = []
        pallete = [
            ('reversed', 'yellow', 'brown'),
            ("image_id", "white", "black"),
            ("image_names", "light red", "black"),
        ]
        self.main_loop = urwid.MainLoop(self.top_widget, palette=pallete, unhandled_input=exit_on_q, handle_mouse=False)

    def run(self):
        self.main_loop.run()

ui = UI()
ui.run()
