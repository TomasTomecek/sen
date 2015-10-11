# sen

Since I started using docker, I always dreamed of having a docker TUI. Something like [tig](https://github.com/jonas/tig), [htop](http://hisham.hm/htop/) or [alot](https://github.com/pazz/alot). Some appeared over time. Such as [docker-mon](https://github.com/icecrime/docker-mon) or [ctop](https://github.com/yadutaf/ctop). Unfortunately, those are not proper docker TUIs. They are meant for monitoring and diagnostics.

So I realized that if I want make my dream come true, I need to do it myself. That's where I started working on *sen* (*dream* in Slovak).

# Installation

`sen` is a python 3 only project. I recommend using at least python 3.4.

## git

```
$ git clone https://github.com/TomasTomecek/sen
$ cd sen
$ ./setup.py install
```

## docker

You can run `sen` from docker container!

```
$ docker build --tag=sen git://github.com/TomasTomecek/sen
$ docker run -v /run/docker.sock:/run/docker.sock -ti -e TERM=$TERM sen
```

# Usage

Bear in mind that unix socket for docker engine needs to be accessible. By default it's located at `/run/docker.sock`.

```
$ sen
```

# Keybindings

## Global

```
N      previous buffer
n      next buffer
x      remove buffer
h, ?   show help
```

## Image commands in listing

```
i      inspect image
d      remove image (irreversible!)
```

## Container commands in listing

```
i      inspect container
l      display logs of container
f      follow logs of container
d      remove container (irreversible!)
s      stop container
t      start container
p      pause container
u      unpause container
X      kill container
```
