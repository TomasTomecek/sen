FROM fedora:22
MAINTAINER Tomas Tomecek <ttomecek@redhat.com> @TomasTomec

RUN dnf install -y python3-pip git python3-urwid python3-docker-py python3-humanize

RUN mkdir /home/sen
WORKDIR /home/sen
COPY . /home/sen

RUN pip3 install .

ENTRYPOINT ["sen"]
