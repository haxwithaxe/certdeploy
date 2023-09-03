"""Tests for the full client docker container."""

import pathlib
import time

import pytest

CERTBOT_HELP_TEXT: bytes = (b'certbot [SUBCOMMAND] [options] [-d DOMAIN] '
                            b'[-d DOMAIN]')


@pytest.mark.certdeploy_docker
@pytest.mark.docker
def test_certbot_passthrough(
    server_docker_container: callable,
    tmp_path: pathlib.Path
):
    """Verify that the container passes through arguments to certbot.

    Note:
        This test uses the `certdeploy-server:latest` on the host system. If
        that doesn't have your latest changes then you need to build a new
        image with `tox -e dockerbuild`.
    """
    ## Setup the server container
    # Get a mock certbot
    server = server_docker_container(
        'certbot_passthrough',
        config=dict(
            fail_fast=True,
            log_level='DEBUG'
        ),
        entrypoint=['/entrypoint.sh', '--help']
    )
    # start and wait for the container to be running and the client to be ready
    server.start(timeout=120)
    time.sleep(1)
    assert CERTBOT_HELP_TEXT in server.logs()
