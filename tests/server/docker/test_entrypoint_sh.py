"""Tests for the entrypoint.sh of the server docker container.

Note:
    These tests use the `certdeploy-server:latest` on the host system. If
    that doesn't have your latest changes then you need to build a new
    image with `tox -e dockerbuild`.
"""

from typing import Callable

import pytest
from fixtures.docker_container import ServerContainer
from fixtures.logging import ServerRefLogMessages as RefMsgs


@pytest.mark.certdeploy_docker
@pytest.mark.docker
def test_certbot_passthrough(
    server_docker_container: Callable[[...], ServerContainer],
):
    """Verify that the container passes through arguments to certbot."""
    # Setup the server container
    server = server_docker_container(
        'certbot_passthrough',
        config=dict(fail_fast=True, log_level='DEBUG'),
        entrypoint=['/entrypoint.sh', '--help'],
    )
    # Start and wait for the target log message to appear
    server.start(timeout=None)
    server.wait_for_log(RefMsgs.CERTBOT_HELP_TEXT.log)
    assert RefMsgs.CERTBOT_HELP_TEXT.log in server.logs()


@pytest.mark.certdeploy_docker
@pytest.mark.docker
def test_renew_when_env(
    server_docker_container: Callable[[...], ServerContainer],
):
    """Verify that the container runs certdeploy-server --renew.

    When the environment variable `CERTDEPLOY_SERVER_RENEW_ONLY` is `"true"`.
    """
    # Setup the server container
    server = server_docker_container(
        'certdeploy_renew_env',
        config=dict(fail_fast=True, log_level='DEBUG'),
        environment={'CERTDEPLOY_SERVER_RENEW_ONLY': 'true'},
    )
    # Start and wait for the target log message to appear
    server.start(timeout=None)
    server.wait_for_log(RefMsgs.RENEW_ONLY.log)
    assert RefMsgs.RENEW_ONLY.log in server.logs()


@pytest.mark.certdeploy_docker
@pytest.mark.docker
def test_runs_daemon_by_default(
    server_docker_container: Callable[[...], ServerContainer],
):
    """Verify that the container runs certdeploy-server --daemon.

    When no arguments are given.
    """
    # Setup the server container
    server = server_docker_container(
        'certdeploy_daemon_default',
        config=dict(fail_fast=True, log_level='DEBUG'),
    )
    # Start and wait for the container and daemon to be running
    server.start(timeout=None)
    server.wait_for_log(RefMsgs.DAEMON_HAS_STARTED.log)
    assert RefMsgs.DAEMON_HAS_STARTED.log in server.logs()


@pytest.mark.certdeploy_docker
@pytest.mark.docker
def test_runs_cli_with_args(
    server_docker_container: Callable[[...], ServerContainer],
):
    """Verify that the container runs the certdeploy-server command.

    When the first argument is `certdeploy-server` the command is called with
    all remaining arguments.
    """
    # Setup the server container
    server = server_docker_container(
        'certdeploy_command_w_args',
        config=dict(fail_fast=True, log_level='DEBUG'),
        entrypoint=['/entrypoint.sh', 'certdeploy-server', '--help'],
    )
    # Start and wait for the target log message to appear
    server.start(timeout=None)
    server.wait_for_log(RefMsgs.HELP_TEXT.log)
    assert RefMsgs.HELP_TEXT.log in server.logs()
