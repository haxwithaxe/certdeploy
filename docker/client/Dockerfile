# Docker Arch (amd64, arm32v6, ...)
ARG TARGET_ARCH=amd64
FROM ${TARGET_ARCH}/python:3.10-alpine

ENV CERTDEPLOY_CLIENT_DAEMON=true

ENTRYPOINT ["/entrypoint.sh"]

COPY ./docker/client/entrypoint.sh /entrypoint.sh
RUN chmod 700 /entrypoint.sh
COPY ./docker/client/conf /etc/certdeploy
RUN mkdir -p /certdeploy/certs /certdeploy/staging
COPY . /certdeploy/src

WORKDIR /certdeploy

RUN apk add --no-cache --virtual .build-deps \
        gcc \
        make \
        linux-headers \
        openssl-dev \
        musl-dev \
        libffi-dev \
        python3-dev \
        cargo \
        git \
    && pip install -e ./src \
    && apk del .build-deps \
    && rm -rf ${HOME}/.cargo
