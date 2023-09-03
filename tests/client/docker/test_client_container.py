"""Tests for the full client docker container."""

import pathlib
import time

import pytest
from fixtures.client_config import client_sftpd_config
from fixtures.docker_container import ContainerStatus


@pytest.mark.certdeploy_docker
@pytest.mark.docker
@pytest.mark.system
@pytest.mark.slow
def test_updates_other_container(
    canned_docker_container: callable,
    client_docker_container: callable,
    mock_server_push: callable,
    tmp_path: pathlib.Path
):
    """Verify that the client container can restart another container.

    Note:
        This test uses the `certdeploy-client:latest` on the host system. If
        that doesn't have your latest changes then you need to build a new
        image with `tox -e dockerbuild`.
    """
    # Setup the canned container to be restarted
    canned = canned_docker_container()
    canned.start()
    ## Setup the client container
    client = client_docker_container(
        'updates_container',
        with_docker=True,
        config=dict(
            update_delay='1s',
            update_services=[dict(type='docker_container', name=canned.name)],
            log_level='DEBUG',
            sftpd=client_sftpd_config(listen_address='0.0.0.0')
        )
    )
    # Take the before measurement
    started_at = canned.started_at
    # Sleep just enough to ensure a definite difference
    time.sleep(1)
    # start and wait for the container to be running and the client to be ready
    client.start(timeout=120)
    context = mock_server_push
    context.pusher(
        lineage_name='test.example.com',
        client_config=client.config,
        client_keypair=client.client_keypair,
        server_keypair=client.server_keypair
    )
    # Wait for the update workflow to finish
    #   Don't wait forever though
    client.wait_for_deployed(timeout=300)
    # Wait for the container to come back up
    canned.wait_for_status(ContainerStatus.RUNNING, timeout=300)
    # Take the after measurement
    restarted_at = canned.started_at
    assert restarted_at != started_at
