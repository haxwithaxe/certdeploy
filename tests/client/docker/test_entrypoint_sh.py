"""Tests for the full client docker container.

Note:
    These tests use the `certdeploy-client:latest` on the host system. If
    that doesn't have your latest changes then you need to build a new
    image with `tox -e dockerbuild`.
"""

from typing import Callable

import pytest
from fixtures.docker_container import ClientContainer
from fixtures.logging import ClientRefLogMessages as RefMsgs


@pytest.mark.certdeploy_docker
@pytest.mark.docker
def test_starts_daemon_by_default(
    client_docker_container: Callable[[...], ClientContainer]
):
    """Verify that the daemon starts by default."""
    # Setup the client container
    client = client_docker_container(
        'entrypoint_sh_default',
        with_docker=True,
        config=dict(log_level='DEBUG'),
    )
    client.start(timeout=300)
    assert RefMsgs.HAS_STARTED.log in client.logs()


@pytest.mark.certdeploy_docker
@pytest.mark.docker
def test_passes_args_to_client(
    client_docker_container: Callable[[...], ClientContainer]
):
    """Verify that args are passed to the client."""
    # Setup the client container
    client = client_docker_container(
        'entrypoint_sh_args',
        config=dict(log_level='DEBUG'),
        entrypoint=['/entrypoint.sh', '--help'],
    )
    client.start(timeout=None)
    client.wait_for_log(RefMsgs.HELP_TEXT.log, timeout=300)
    assert RefMsgs.HELP_TEXT.log in client.logs()
