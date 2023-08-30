"""Tests for `certdeploy.client.update.update_docker_container`."""

import time

import pytest
from fixtures.docker_container import ContainerStatus

from certdeploy.client.config.service import DockerContainer
from certdeploy.client.errors import DockerContainerNotFound
from certdeploy.client.update import update_docker_container


@pytest.mark.docker
def test_updates_docker_container_by_name(
        canned_docker_container: callable,
        tmp_client_config: callable
):
    """Verify the client can update a container.

    Verify the client can update a container based on the container's name.
    """
    client_config = tmp_client_config(
        docker_url='unix://var/run/docker.sock',
        fail_fast=True
    )
    canned = canned_docker_container()
    # Take the before measurement
    started_at = canned.started_at
    # Sleep just enough to ensure a definite difference
    time.sleep(1)
    # Do the thing under test
    update_docker_container(
        DockerContainer({'name': canned.name}),
        client_config
    )
    # Wait for the container to come back up
    canned.wait_for_status(ContainerStatus.RUNNING, timeout=300)
    # Take the after measurement
    restarted_at = canned.started_at
    assert restarted_at != started_at


@pytest.mark.docker
def test_updates_docker_container_by_filter(
        canned_docker_container: callable,
        tmp_client_config: callable
):
    """Verify that the client can update a container based on filters."""
    client_config = tmp_client_config(
        docker_url='unix://var/run/docker.sock',
        fail_fast=True
    )
    canned = canned_docker_container()
    # Take the before measurement
    started_at = canned.started_at
    # Sleep just enough to ensure a definite difference
    time.sleep(1)
    # Do the thing under test
    update_docker_container(
        DockerContainer({'filters': {'label': 'certdeploy_test'}}),
        client_config
    )
    # Wait for the container to come back up
    canned.wait_for_status(ContainerStatus.RUNNING, timeout=300)
    # Take the after measurement
    restarted_at = canned.started_at
    assert restarted_at != started_at


@pytest.mark.docker
def test_fail_fast_docker_container(
        canned_docker_container: callable,
        tmp_client_config: callable
):
    """Verify that the client fails fast."""
    client_config = tmp_client_config(
        docker_url='unix://var/run/docker.sock',
        fail_fast=True
    )
    # Do the thing under test
    with pytest.raises(DockerContainerNotFound):
        update_docker_container(
            DockerContainer({'filters': {'name': 'doesn\'t exist'}}),
            client_config
        )
