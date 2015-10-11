FROM fedora:22
MAINTAINER Tomasko

RUN dnf install -y python3-pip git python3-urwid python3-docker-py python3-humanize

RUN pip3 install git+https://github.com/TomasTomecek/sen

CMD sen
