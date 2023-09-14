"""Tests for the full server docker container.

Note:
    These tests use the `certdeploy-server:latest` on the host system. If
    that doesn't have your latest changes then you need to build a new
    image with `tox -e dockerbuild`.
"""

import pathlib

import pytest

CERTBOT_HELP_TEXT: bytes = (b'certbot [SUBCOMMAND] [options] [-d DOMAIN] '
                            b'[-d DOMAIN]')
CERTDEPLOY_RENEW_TEXT: bytes = b'DEBUG:certdeploy-server: Running renew'
CERTDEPLOY_DAEMON_TEXT: bytes = b'DEBUG:certdeploy-server: Running daemon'
CERTDEPLOY_HELP_TEXT: bytes = b'Usage: certdeploy-server [OPTIONS]'


@pytest.mark.certdeploy_docker
@pytest.mark.docker
def test_certbot_passthrough(
    server_docker_container: callable,
    tmp_path: pathlib.Path
):
    """Verify that the container passes through arguments to certbot."""
    # Setup the server container
    server = server_docker_container(
        'certbot_passthrough',
        config=dict(
            fail_fast=True,
            log_level='DEBUG'
        ),
        entrypoint=['/entrypoint.sh', '--help']
    )
    # Start and wait for the target log message to appear
    server.start(timeout=None)
    server.wait_for_log(CERTBOT_HELP_TEXT)
    assert CERTBOT_HELP_TEXT in server.logs()


@pytest.mark.certdeploy_docker
@pytest.mark.docker
def test_renew_when_env(
    server_docker_container: callable,
    tmp_path: pathlib.Path
):
    """Verify that the container runs certdeploy-server --renew.

    When the environment variable `CERTDEPLOY_SERVER_RENEW_ONLY` is `"true"`.
    """
    # Setup the server container
    server = server_docker_container(
        'certdeploy_renew_env',
        config=dict(
            fail_fast=True,
            log_level='DEBUG'
        ),
        environment={'CERTDEPLOY_SERVER_RENEW_ONLY': 'true'}
    )
    # Start and wait for the target log message to appear
    server.start(timeout=None)
    server.wait_for_log(CERTDEPLOY_RENEW_TEXT)
    assert CERTDEPLOY_RENEW_TEXT in server.logs()


@pytest.mark.certdeploy_docker
@pytest.mark.docker
def test_runs_daemon_by_default(
    server_docker_container: callable,
    tmp_path: pathlib.Path
):
    """Verify that the container runs certdeploy-server --daemon.

    When no arguments are given.
    """
    # Setup the server container
    server = server_docker_container(
        'certdeploy_daemon_default',
        config=dict(
            fail_fast=True,
            log_level='DEBUG'
        )
    )
    # Start and wait for the container and daemon to be running
    server.start(timeout=None)
    server.wait_for_log(CERTDEPLOY_DAEMON_TEXT)
    assert CERTDEPLOY_DAEMON_TEXT in server.logs()


@pytest.mark.certdeploy_docker
@pytest.mark.docker
def test_runs_cli_with_args(
    server_docker_container: callable,
    tmp_path: pathlib.Path
):
    """Verify that the container runs the certdeploy-server command.

    When the first argument is `certdeploy-server` the command is called with
    all remaining arguments.
    """
    # Setup the server container
    server = server_docker_container(
        'certdeploy_command_w_args',
        config=dict(
            fail_fast=True,
            log_level='DEBUG'
        ),
        entrypoint=['/entrypoint.sh', 'certdeploy-server', '--help']
    )
    # Start and wait for the target log message to appear
    server.start(timeout=None)
    server.wait_for_log(CERTDEPLOY_HELP_TEXT)
    assert CERTDEPLOY_HELP_TEXT in server.logs()
