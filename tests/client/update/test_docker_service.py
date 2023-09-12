"""Tests for `certdeploy.client.update.update_docker_service`."""

import time

import pytest
from fixtures.docker_service import ServiceWrapper

from certdeploy.client.config.service import DockerService
from certdeploy.client.errors import DockerServiceNotFound
from certdeploy.client.update import update_docker_service


@pytest.mark.docker
@pytest.mark.swarm
def test_updates_docker_service_by_name(
        canned_docker_service: ServiceWrapper,
        tmp_client_config: callable
):
    """Verify the client can update a docker service.

    Verify the client can update a service based on the docker service's
    name.
    """
    client_config = tmp_client_config(
        docker_url='unix://var/run/docker.sock',
        fail_fast=True
    )
    # Sleep just enough to ensure a definite difference
    time.sleep(1)
    # Do the thing under test
    update_docker_service(
        DockerService({'name': canned_docker_service.name}),
        client_config
    )
    assert canned_docker_service.updated_at != canned_docker_service.created_at


@pytest.mark.docker
@pytest.mark.swarm
def test_updates_docker_service_by_filter(
        canned_docker_service: ServiceWrapper,
        tmp_client_config: callable
):
    """Verify that the client can update a service based on filters."""
    client_config = tmp_client_config(
        docker_url='unix://var/run/docker.sock',
        fail_fast=True
    )
    # Sleep just enough to ensure a definite difference
    time.sleep(1)
    # Do the thing under test
    update_docker_service(
        DockerService({'filters': {'label': 'certdeploy_test'}}),
        client_config
    )
    assert canned_docker_service.updated_at != canned_docker_service.created_at


@pytest.mark.skip(reason='broken by https://github.com/moby/moby/issues/46341')
@pytest.mark.docker
@pytest.mark.swarm
def test_updates_docker_service_by_filter_with_regex(
        canned_docker_service: ServiceWrapper,
        tmp_client_config: callable
):
    """Verify that the client can update a service based on filters.

    Verify that the client can update a service based on filters explicitly
    using regex. This is in response to a docker bug
    (https://github.com/moby/moby/issues/46341).
    """
    client_config = tmp_client_config(
        docker_url='unix://var/run/docker.sock',
        fail_fast=True
    )
    # Sleep just enough to ensure a definite difference
    time.sleep(1)
    # Do the thing under test
    update_docker_service(
        DockerService({'filters': {'label': 'certdeploy_tes.*'}}),
        client_config
    )
    assert canned_docker_service.updated_at != canned_docker_service.created_at


@pytest.mark.docker
@pytest.mark.swarm
def test_fail_fast_docker_service(
        canned_docker_service: ServiceWrapper,
        tmp_client_config: callable
):
    """Verify that the client fails fast."""
    client_config = tmp_client_config(
        docker_url='unix://var/run/docker.sock',
        fail_fast=True
    )
    # Do the thing under test
    with pytest.raises(DockerServiceNotFound) as err:
        update_docker_service(
            DockerService({'filters': {'label': 'doesn\'t exist'}}),
            client_config
        )
    msg = ('<ExceptionInfo DockerServiceNotFound(\'DockerService failed to '
           'update: Could not find any docker service matching the following '
           'filter: {\\\'label\\\': "doesn\\\'t exist"}\')')
    assert msg in str(err)
