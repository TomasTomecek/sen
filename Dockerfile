FROM alpine:3.14
MAINTAINER Tomas Tomecek <tomas@tomecek.net>

LABEL RUN docker run -v /var/run/docker.sock:/run/docker.sock -ti -e TERM --name \${NAME} \${IMAGE}

COPY . /home/sen

RUN apk update \
    && apk add python3 py3-pip \
    && apk add -t build python3-dev py3-pip libc-dev gcc git \
    && pip install urwid \
    && pip install -r /home/sen/requirements.txt \
    && pip install /home/sen \
    && apk del --purge build python3-dev libc-dev gcc sqlite-libs git \
    && rm /var/cache/apk/*

ENV DOCKER_HOST http+unix://run/docker.sock

CMD ["sen"]
