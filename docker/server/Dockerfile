# Docker Arch (amd64, arm32v6, ...)
ARG TARGET_ARCH=amd64
FROM ${TARGET_ARCH}/python:3.10-alpine3.18

ENTRYPOINT [ "/entrypoint.sh" ]
RUN mkdir -p /var/run/certdeploy

COPY ./docker/server/entrypoint.sh /entrypoint.sh
RUN chmod 700 /entrypoint.sh
RUN mkdir /certdeploy
COPY ./dist /certdeploy/dist
COPY ./docker/server/conf /etc/certdeploy
RUN mkdir -p /etc/letsencrypt/renewal-hooks/deploy

WORKDIR /certdeploy

# Install certbot runtime dependencies
RUN apk add --no-cache \
        libffi \
        libssl1.1 \
        openssl \
        ca-certificates \
        binutils

# We set this environment variable and install git while building to try and
# increase the stability of fetching the rust crates needed to build the
# cryptography library
ARG CARGO_NET_GIT_FETCH_WITH_CLI=true
# Install certbot and certdeploy
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
    && pip install certbot \
    && pip install /certdeploy/dist/certdeploy-*.whl \
    && ln -s /usr/local/bin/certdeploy-server /etc/letsencrypt/renewal-hooks/deploy/certdeploy-hook \
    && apk del .build-deps \
    && rm -rf ${HOME}/.cargo /certdeploy/dist
