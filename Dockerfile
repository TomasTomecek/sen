FROM alpine:3.2
MAINTAINER Tomas Tomecek <ttomecek@redhat.com> @TomasTomec

COPY . /home/sen

RUN apk -U add python3 \
	&& apk add -t build python3-dev libc-dev gcc \
	&& pip3 install /home/sen \
	&& apk del --purge build \
	&& rm /var/cache/apk/*

ENV DOCKER_HOST http+unix://run/docker.sock

ENTRYPOINT ["sen"]
