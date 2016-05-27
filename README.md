# sen

[![Code Issues](https://www.quantifiedcode.com/api/v1/project/5282fc57c1094698b39071d98c76cdb6/badge.svg)](https://www.quantifiedcode.com/app/project/5282fc57c1094698b39071d98c76cdb6)
[![Circle CI](https://circleci.com/gh/TomasTomecek/sen.svg?style=svg)](https://circleci.com/gh/TomasTomecek/sen)

`sen` is a terminal user interface for docker engine:
 * it can interactively manage your containers and images:
  * manage? start, stop, restart, kill, delete,...
 * there is a "dashboard" view for containers and images
 * you are able to inspect containers and images
 * sen can fetch logs of containers and even stream logs real-time
 * buffers support searching and filtering
 * sen receives real-time updates from docker when anything changes
  * e.g. if you pull a container in another terminal, sen will pick it up
 * sen notifies you whenever something happens (and reports slow queries)
 * supports a lot of vim-like keybindings (`j`, `k`, `gg`, `/`, ...)
 * you can get interactive tree view of all images (equivalent of `docker images --tree`)

You can [see the features yourself](/docs/features.md).

![Preview of sen](/data/sen-preview.gif)

# Installation and running `sen`

I strongly advise to run `sen` from a docker container provided on docker hub:

```
$ docker pull tomastomecek/sen
```

This repository has set up automated builds on docker hub. In case you run into some issue, try pulling latest version first before opening an issue.

This is the recommended way of running `sen` in a container:

```
$ docker run --privileged -v /var/run/docker.sock:/run/docker.sock -ti -e TERM tomastomecek/sen
```

Some distros have `/var/run` simlinked to `/run`, so you can do `/run/docker.sock:/run/docker.sock` instead.

In case you would like to try development version of sen, you can pull `tomastomecek/sen:dev`.


## docker

You can easily build a docker image with sen inside:

```
$ docker build --tag=$USER/sen https://github.com/tomastomecek/sen
$ docker run --privileged -v /var/run/docker.sock:/run/docker.sock -ti -e TERM $USER/sen
```


## PyPI

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
$ ./setup.py install
$ sen
```

Or even run `sen` straight from git:

```
$ git clone https://github.com/TomasTomecek/sen
$ cd sen
$ PYTHONPATH="$PWD:$PYTHONPATH" ./sen/cli.py
```


# Prerequisite

Either:

* The unix socket for docker engine needs to be accessible. By default it's located at `/run/docker.sock`.

Or:

* Have the `DOCKER_HOST`, `DOCKER_TLS_VERIFY`, and `DOCKER_CERT_PATH` set properly.  If you're using `docker-machine` or `boot2docker` you're all set!


# Keybindings

Since I am heavy `vim` user, these keybindings are trying to stay close to vim.


## Global

```
/      search (provide empty query to disable searching)
n      next search occurrence
N      previous search occurrence
f4     display only lines matching provided query (provide empty query to clear filtering)
        * main listing provides additional filtering (for more info, check Listing Section)
        * example query: "fed" - display lines containing string "fed"
f5     open a tree view of all images (`docker images --tree` equivalent)
ctrl o next buffer
ctrl i previous buffer
x      remove buffer
ctrl l redraw user interface
h, ?   show help
```

## Movement

```
gg     go to first item
G      go to last item
j      go one line down
k      go one line up
pg up
ctrl u go 10 lines up
pg down
ctrl d go 10 lines down
```

## Listing

```
@      refresh listing
f4     display only lines matching provided query (provide empty query to clear filtering)
        * space-separated list of query strings, currently supported filters are:
           * t[ype]=c[ontainer[s]]
           * t[ype]=i[mage[s]]
           * s[tate]=r[unning])
          example query may be:
           * "type=container" - show only containers (short equivalent is "t=c")
           * "type=image fedora" - show images with string "fedora" in name (equivalent "t=i fedora")
```

## Image commands in listing

```
i      inspect image
d      remove image (irreversible!)
enter  display detailed info about image (when layer is focused)
```

## Container commands in listing

```
i      inspect container
l      display logs of container
f      follow logs of container
d      remove container (irreversible!)
t      stop container
s      start container
r      restart container
p      pause container
u      unpause container
b      open container's mapped ports in a web-browser
X      kill container
!      toggle realtime updates of the interface (this is useful when you are removing multiple
       objects and don't want the listing change during that so you accidentally remove something)
```

## Tree buffer

```
enter  display detailed info about image (opens image info buffer)
```

## Image info buffer

```
d      remove image tag (when image name is focused)
enter  display detailed info about image (when layer is focused)
i      inspect image (when layer is focused)
```


# Why I started sen?

Since I started using docker, I always dreamed of having a docker TUI. Something like [tig](https://github.com/jonas/tig), [htop](http://hisham.hm/htop/) or [alot](https://github.com/pazz/alot). Some appeared over time. Such as [docker-mon](https://github.com/icecrime/docker-mon) or [ctop](https://github.com/yadutaf/ctop). Unfortunately, those are not proper docker TUIs. They are meant for monitoring and diagnostics.

So I realized that if I want make my dream come true, I need to do it myself. That's where I started working on *sen* (*dream* in Slovak).

