# sen

[![Code Issues](https://www.quantifiedcode.com/api/v1/project/5282fc57c1094698b39071d98c76cdb6/badge.svg)](https://www.quantifiedcode.com/app/project/5282fc57c1094698b39071d98c76cdb6)
[![Circle CI](https://circleci.com/gh/TomasTomecek/sen.svg?style=svg)](https://circleci.com/gh/TomasTomecek/sen)

Since I started using docker, I always dreamed of having a docker TUI. Something like [tig](https://github.com/jonas/tig), [htop](http://hisham.hm/htop/) or [alot](https://github.com/pazz/alot). Some appeared over time. Such as [docker-mon](https://github.com/icecrime/docker-mon) or [ctop](https://github.com/yadutaf/ctop). Unfortunately, those are not proper docker TUIs. They are meant for monitoring and diagnostics.

So I realized that if I want make my dream come true, I need to do it myself. That's where I started working on *sen* (*dream* in Slovak).

![sen preview](/data/sen-preview.png)

# Installation

I strongly advise to run `sen` from a docker container. This repository has set up automated builds on docker hub. In case you run into some issue, try pulling latest version before opening issue. At some point, I'll start with releasing and versioning.

```
$ docker run -v /run/docker.sock:/run/docker.sock -ti -e TERM=$TERM tomastomecek/sen
```


## git

`sen` is a python 3 only project. I recommend using at least python 3.4.

```
$ git clone https://github.com/TomasTomecek/sen
$ cd sen
$ ./setup.py install
```

## docker

```
$ docker build --tag=sen git://github.com/tomastomecek/sen
$ docker run -v /run/docker.sock:/run/docker.sock -ti -e TERM=$TERM sen
```

# Usage

Bear in mind that unix socket for docker engine needs to be accessible. By default it's located at `/run/docker.sock`.

```
$ sen
```

# Keybindings

Since I am heavy `vim` user, these keybindings are trying to stay close to vim.

## Global

```
/      search
n      next search occurrence
N      previous search occurrence
f4     filter items in list (space-separated list of query strings, currently supported:
         c[ontainer[s]], i[mage[s]], r[unning])
ctrl o next buffer
ctrl i previous buffer
x      remove buffer
@      refresh listing
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
r      restart container
p      pause container
u      unpause container
X      kill container
```
