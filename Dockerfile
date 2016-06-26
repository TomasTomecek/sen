FROM alpine:3.4
MAINTAINER Tomas Tomecek <ttomecek@redhat.com> @TomasTomec

LABEL RUN docker run --privileged -v /run/docker.sock:/run/docker.sock -ti -e TERM --name \${NAME} \${IMAGE}

COPY . /home/sen

RUN apk update \
    && apk add python3 \
    && apk add -t build python3-dev libc-dev gcc git \
    && pip3 install urwid \
    && pip3 install -r /home/sen/requirements.txt \
    && pip3 install /home/sen \
    && apk del --purge build python3-dev libc-dev gcc sqlite-libs git \
    && rm /var/cache/apk/*

ENV DOCKER_HOST http+unix://run/docker.sock

CMD ["sen"]
