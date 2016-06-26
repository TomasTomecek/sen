FROM fedora:24
MAINTAINER Tomas Tomecek <ttomecek@redhat.com> @TomasTomec

LABEL RUN docker run --privileged -v /run/docker.sock:/run/docker.sock -ti -e TERM --name \${NAME} \${IMAGE}

RUN dnf install -y python3-pip git python3-urwid python3-urwidtrees python3-docker-py && dnf clean all

RUN mkdir /home/sen
WORKDIR /home/sen
COPY . /home/sen

RUN pip3 install -r ./requirements.txt
RUN pip3 install .

CMD ["sen"]
