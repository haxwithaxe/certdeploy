"""Tests for the full server docker container.

Note:
    These tests use the `certdeploy-server:latest` on the host system. If
    that doesn't have your latest changes then you need to build a new
    image with `tox -e dockerbuild`.
"""

import pathlib
import time
from datetime import datetime
from typing import Callable

import pytest
from fixtures.docker_container import (
    ClientContainer,
    ContainerInternalPaths,
    ContainerStatus,
    ContainerWrapper,
    ServerContainer
)
from fixtures.keys import KeyPair
from fixtures.server_config import client_conn_config


@pytest.mark.certdeploy_docker
@pytest.mark.docker
@pytest.mark.system
@pytest.mark.slow
def test_pushes_to_clients(
    canned_docker_container: Callable[[...], ContainerWrapper],
    client_docker_container: Callable[[...], ClientContainer],
    lineage_factory: Callable[[str, list[str]], pathlib.Path],
    keypairgen: Callable[[...], KeyPair],
    server_docker_container: Callable[[...], ServerContainer],
    tmp_path: pathlib.Path
):
    """Verify that the server pushes and the client updates."""
    client_keypair = keypairgen()
    server_keypair = keypairgen()
    client1_tmp_path = tmp_path.joinpath('client1')
    client1_tmp_path.mkdir()
    client2_tmp_path = tmp_path.joinpath('client2')
    client2_tmp_path.mkdir()
    server_tmp_path = tmp_path.joinpath('server')
    server_tmp_path.mkdir()
    lineage_files = ['fullchain.pem', 'privkey.pem']
    lineage_files.sort()  # Presorting for comparisons
    lineage_name = 'test.example.com'
    lineage_container_path = ContainerInternalPaths.lineages.joinpath(
        lineage_name
    )
    canned_containers = []
    clients = []
    client_configs = []
    start_times: dict[str, datetime] = {}
    for index in range(2):
        client_tmp_path = tmp_path.joinpath(f'client_{index}')
        client_tmp_path.mkdir()
        canned = canned_docker_container(started=True, suffix=f'_{index}')
        canned_containers.append(canned)
        # Record the start time for each container
        start_times[canned.name] = canned.started_at
        # Setup a client container
        client = client_docker_container(
            f'pushes_to_clients_target{index}',
            client_keypair=client_keypair.copy(),
            server_keypair=server_keypair.copy(),
            tmp_path=client_tmp_path,
            with_docker=True,
            config=dict(
                fail_fast=True,
                update_delay='1s',  # Set to 1s to speed up the test
                update_services=[dict(type='docker_container',
                                      name=canned.name)],
                # SFTPD needs to listen on the external address of the
                #   container. localhost is used as the default elsewhere in
                #   the test fixtures.
                sftpd=dict(listen_address='0.0.0.0')
            )
        )
        clients.append(client)
        client.start()
        # Populate the client connection configs for the server
        client_configs.append(
            client_conn_config(
                client_keypair=client.client_keypair,
                address=client.ipv4_address,
                domains=[lineage_name],
                port=client.config['sftpd']['listen_port'],
                path=client.config['source']
            )
        )
    ## Setup the server container
    server = server_docker_container(
        'pushes_to_clients',
        client_keypair=client_keypair.copy(),
        server_keypair=server_keypair,
        lineage_name=lineage_name,
        lineage_filenames=lineage_files,
        tmp_path=server_tmp_path,
        config=dict(
            fail_fast=True,
            client_configs=client_configs
        ),
        environment={
            'CERTDEPOLY_SERVER_PUSH_ONLY': True,
            'RENEWED_LINEAGE': str(lineage_container_path),
            'RENEWED_DOMAINS': lineage_name
        }
    )
    # Sleep to guarantee at least a 1 second gap between the canned containers
    #   starting and the server pushing
    time.sleep(1)
    # Start and don't bother waiting for startup
    server.start(timeout=None)
    # Wait for the container to be done.
    server.wait_for_status(ContainerStatus.EXITED, ContainerStatus.DEAD,
                           timeout=120)
    assert server.attrs['State']['ExitCode'] == 0, \
        f'Server exited nonzero. Test is invalid.\n{server.logs().decode()}'
    ## Verify the results
    # For each client check for the PEM files that should have been pushed
    for client in clients:
        client.wait_for_updated(timeout=120)
        pem_files = client.output_path.joinpath(lineage_name).rglob('*.pem')
        output = [x.name for x in pem_files]
        output.sort()
        assert output == lineage_files
        # Just in case the tmpdir doesn't get rotated for some reason. It seems
        #   to happen occasionally.
        for path in pem_files:
            path.unlink()
    # For each canned container verify that it was updated
    for canned in canned_containers:
        assert (canned.started_at - start_times[canned.name]).seconds >= 1
