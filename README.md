# sen

![Build Status](https://travis-ci.org/TomasTomecek/sen.svg?branch=master)


`sen` is a terminal user interface for containers:
 * it can interactively manage your containers and images:
  * start, stop, restart, kill, delete,...
 * there is a "dashboard" view for containers and images
 * you are able to inspect containers and images
 * sen can fetch logs of containers and even stream logs real-time
 * some buffers support searching and filtering
 * sen receives real-time updates from docker when anything changes
  * e.g. if you pull a container in another terminal, sen will pick it up
 * sen notifies you whenever something happens (and reports slow queries)
 * supports a lot of vim-like keybindings (`j`, `k`, `gg`, `/`, ...)
 * you can get interactive tree view of all images (equivalent of `docker images --tree`)
 * see how much space containers, images and volumes occupy (just type `:df`)

You can [see the features yourself](/docs/features.md).

![Preview of sen](/data/sen-preview.gif)


# Status

**maintenance mode**

I lost interest in working on new features for sen. I will continue providing
support for sen as much as I can, but only bug fixes. Please don't expect any
new features written by me. If you want some feature in sen, you need to write
it yourself — I will gladly accept such pull request.


# Installation and running `sen`

I strongly advise to run `sen` from a docker container provided on docker hub:

```
$ docker pull tomastomecek/sen
```

This repository has set up automated builds on docker hub. In case you run into some issue, try pulling latest version first before opening an issue.

This is the recommended way of running `sen` in a container:

```
$ docker run -v /var/run/docker.sock:/run/docker.sock -ti -e TERM tomastomecek/sen
```

Some distros have `/var/run` simlinked to `/run`, so you can do `/run/docker.sock:/run/docker.sock` instead.

In case you would like to try development version of sen, you can pull `tomastomecek/sen:dev`.


## docker

You can easily build a docker image with sen inside:

```
$ docker build --tag=$USER/sen https://github.com/tomastomecek/sen
$ docker run -v /var/run/docker.sock:/run/docker.sock -ti -e TERM $USER/sen
```


## PyPI

`sen` is using [`urwidtrees`](https://github.com/pazz/urwidtrees) as a dependency. Unfortunately, the upstream
maintainer doesn't maintain it on PyPI so we need to install it directly from
git, before installing sen (the forked PyPI version has a [bug](https://github.com/TomasTomecek/sen/issues/128) in
the installation process):

```
$ pip3 install git+https://github.com/pazz/urwidtrees.git@9142c59d3e41421ff6230708d08b6a134e0a8eed#egg=urwidtrees-1.0.3.dev
```

`sen` releases are available on PyPI:

```
$ pip3 install sen
```

If `pip3` executable is not available on your system, you can run pip like this:

```
$ python3 -m pip install sen
```

And then start sen like this:

```
$ sen
```


## git

`sen` is a python 3 only project. I recommend using at least python 3.4. This is how you can install `sen` from git:

```
$ git clone https://github.com/TomasTomecek/sen
$ cd sen
$ pip3 install --user -r ./requirements.txt
$ ./setup.py install
$ sen
```

Or even run `sen` straight from git:

```
$ git clone https://github.com/TomasTomecek/sen
$ cd sen
$ pip3 install --user -r ./requirements.txt
$ PYTHONPATH="$PWD:$PYTHONPATH" ./sen/cli.py
```


# Prerequisite

Either:

* The unix socket with the API for docker engine needs to be accessible. By default it's located at `/run/docker.sock`.

Or:

* Have the `DOCKER_HOST`, `DOCKER_TLS_VERIFY`, and `DOCKER_CERT_PATH` set properly.


# Podman

Starting Podman v2.0, there is a [Docker-compatible
API](https://docs.podman.io/en/latest/_static/api.html) provided by Podman.
`sen` works well while talking to Podman over this API.


## Connecting to Podman

Run Podman as:
```
$ podman system service -t 0
```

Let's discover the unix socket path now:
```
$ podman info --format={{".Host.RemoteSocket.Path"}}
/run/user/1000/podman/podman.sock
```

And finally tell `sen` to connect to it:
```
$ DOCKER_HOST=unix://$(podman info --format={{".Host.RemoteSocket.Path"}}) sen
```


# Keybindings

Since I am heavy `vim` user, these keybindings are trying to stay close to vim.


## Global

```
/         search (provide empty query to disable searching)
n         next search occurrence
N         previous search occurrence
f4        display only lines matching provided query (provide empty query to clear filtering)
f5        open a tree view of all images (`docker images --tree` equivalent)
ctrl o    navigate to next buffer
ctrl i    navigate to previous buffer
x         remove buffer
q         remove buffer, quit if no buffer is left
ctrl l    redraw user interface
h, ?      show help
:         open command prompt
```

## Movement

```
gg, home  go to first item
G, end    go to last item
j         go one line down
k         go one line up
pg up
ctrl u    go 10 lines up
pg down
ctrl d    go 10 lines down
```

## Listing

```
@         refresh listing
f4        filtering, for more info run `help filter` in sen
```

## Image commands in listing

```
i         inspect image
d         remove image (irreversible!)
D         remove image forcibly (irreversible!)
enter     display detailed info about image (when layer is focused)
```

## Container commands in listing

```
i         inspect container
l         display logs of container
f         follow logs of container
d         remove container (irreversible!)
D         remove container forcibly (irreversible!)
t         stop container
s         start container
r         restart container
p         pause container
u         unpause container
b         open container's mapped ports in a web-browser
X         kill container
!         toggle realtime updates of the interface (this is useful when you are removing multiple
          objects and don't want the listing change during that so you accidentally remove something)
```

## Tree buffer

```
enter  display detailed info about image (opens image info buffer)
```

## Image info buffer

```
enter     display detailed info about image (when an image is focused)
i         inspect image or container, whatever is focused
```


## Container info buffer

```
enter     display detailed info about image (when image of the container is focued)
i         inspect image (when image of the container is focued)
```


## Disk usage buffer

You can enter it by typing command `df`.


# Why I started sen?

Since I started using docker, I always dreamed of having a docker TUI.
Something like [tig](https://github.com/jonas/tig),
[htop](http://hisham.hm/htop/) or [alot](https://github.com/pazz/alot). Some
appeared over time. Such as
[docker-mon](https://github.com/icecrime/docker-mon) or
[ctop](https://github.com/yadutaf/ctop). Unfortunately, those are not proper
docker TUIs. They are meant for monitoring and diagnostics.

So I realized that if I want make my dream come true, I need to do it myself.
That's where I started working on *sen* (*dream* in Slovak).

But! As the time went, [someone](https://github.com/moncho) else had the same
idea as I did: [dry](https://github.com/moncho/dry).
