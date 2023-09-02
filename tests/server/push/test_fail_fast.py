"""Tests for the `fail_fast` config in push operations."""

import paramiko
import pytest

from certdeploy.server.server import PushMode, Server


def test_fail_fast_on_serial_push(
        mock_fail_client: callable,
        tmp_server_config: callable,
        client_conn_config_factory: callable,
        lineage_factory: callable
):
    """Verify that the `fail_fast` config causes early exit."""
    ## Define some variables to avoid magic values
    client_address = '127.0.0.1'
    lineage_name = 'lineage.test'
    # Set to more than one to verify the server fails on the first error
    push_retries = 3
    ## Setup client
    # Shared client key pair
    client0_server = mock_fail_client(client_address)
    client0_config = client_conn_config_factory(
        address=client0_server.address,
        port=client0_server.port,
        domains=[lineage_name]
    )
    client1_server = mock_fail_client(client_address)
    client1_config = client_conn_config_factory(
        address=client1_server.address,
        port=client1_server.port,
        domains=[lineage_name]
    )
    ## Setup server
    server_config = tmp_server_config(
        client_configs=[client0_config, client1_config],
        fail_fast=True,
        push_mode=PushMode.SERIAL.value,
        push_retries=push_retries
    )
    ## Setup the lineage
    # The filename doesn't matter because it will never get far enough to
    #   matter.
    lineage_path = str(lineage_factory(lineage_name, ['doesnotmatter.pem']))
    ## Setup test
    server = Server(server_config)
    server.sync(lineage_path, [lineage_name])
    ## Run test
    with pytest.raises(paramiko.ssh_exception.SSHException) as err:
        server.serve_forever(one_shot=True)
    ## Verify results
    # Server raises the right exception given the mock client
    assert 'Error reading SSH protocol banner' in str(err)
    # First client has a connection attempt
    assert len(client0_server.log) == 1
    # Second client never gets a connection attempt
    assert len(client1_server.log) == 0


def test_fail_fast_on_parallel_push(
        mock_fail_client: callable,
        tmp_server_config: callable,
        client_conn_config_factory: callable,
        lineage_factory: callable
):
    """Verify that the `fail_fast` config causes earlyish exit.

    The expected behavior is that both push workers will finish because they
    finish so quickly against the mock clients. The first one to be joined
    will raise an exception.
    """
    ## Define some variables to avoid magic values
    client_address = '127.0.0.1'
    lineage_name = 'lineage.test'
    # Set to more than one to verify the server fails on the first error
    push_retries = 3
    ## Setup client
    client0_server = mock_fail_client(client_address)
    client0_config = client_conn_config_factory(
        address=client0_server.address,
        port=client0_server.port,
        domains=[lineage_name]
    )
    client1_server = mock_fail_client(client_address)
    client1_config = client_conn_config_factory(
        address=client1_server.address,
        port=client1_server.port,
        domains=[lineage_name]
    )
    ## Setup server
    server_config = tmp_server_config(
        client_configs=[client0_config, client1_config],
        fail_fast=True,
        push_mode=PushMode.PARALLEL.value,
        push_retries=push_retries
    )
    ## Setup the lineage
    # The filename doesn't matter because it will never get far enough to
    #   matter.
    lineage_path = str(lineage_factory(lineage_name, ['doesnotmatter.pem']))
    ## Setup test
    server = Server(server_config)
    server.sync(lineage_path, [lineage_name])
    ## Run test
    with pytest.raises(paramiko.ssh_exception.SSHException) as err:
        server.serve_forever(one_shot=True)
    ## Verify the results
    # Server raises the right exception given the mock client
    assert 'Error reading SSH protocol banner' in str(err)
    # First client has a connection attempt
    assert len(client0_server.log) == 1
    # Second client never gets a connection attempt
    assert len(client1_server.log) == 1
