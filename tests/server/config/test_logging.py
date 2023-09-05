"""Check that the various logging configs do what they say they do."""
import pathlib
from typing import Callable

import pytest
from fixtures.mock_fail_client import MockClientTCPServer

from certdeploy.server.config import ServerConfig
from certdeploy.server.server import Server

_TEST_LINEAGE_NAME = 'lineage.test'


@pytest.fixture()
def canned_client_conn_config(
    client_conn_config_factory: Callable[[...], dict],
    mock_fail_client: Callable[[...], MockClientTCPServer]
) -> dict:
    """Return a canned client connection config `dict` for these tests."""
    client_server = mock_fail_client('127.0.0.1')
    client_config = client_conn_config_factory(
        address=client_server.address,
        port=client_server.port,
        domains=[_TEST_LINEAGE_NAME],
        push_retries=0
    )
    return client_config


def test_logs_to_given_file(
    mock_fail_client: Callable[[...], MockClientTCPServer],
    canned_client_conn_config: dict,
    lineage_factory: Callable[[...], pathlib.Path],
    tmp_server_config: Callable[[...], ServerConfig],
    tmp_path: pathlib.Path
):
    """Verify the `log_filename` config changes where the server logs."""
    ## Define some variables to avoid magic values
    log_path = tmp_path.joinpath('sftp.log')
    ## Setup Server
    server_config = tmp_server_config(
        client_configs=[canned_client_conn_config],
        push_retries=0,
        push_interval=0,
        log_level='ERROR',
        sftp_log_level='CRITICAL',
        log_filename=str(log_path),
        sftp_log_filename='/dev/null'
    )
    ## Setup lineage
    # The filename doesn't matter because it will never get far enough to
    #   matter.
    lineage_path = lineage_factory(_TEST_LINEAGE_NAME, ['doesnotmatter.pem'])
    ## Setup test
    server = Server(server_config)
    server.sync(str(lineage_path), [_TEST_LINEAGE_NAME])
    ## Run test
    server.serve_forever(one_shot=True)
    ## Verify results
    assert 'ERROR' in log_path.read_text()


def test_logs_at_given_level(
    mock_fail_client: Callable[[...], MockClientTCPServer],
    client_conn_config_factory: Callable[[...], dict],
    lineage_factory: Callable[[...], pathlib.Path],
    tmp_server_config: Callable[[...], ServerConfig],
    tmp_path: pathlib.Path
):
    """Verify the `log_level` config changes what the server logs."""
    ## Define some variables to avoid magic values
    client_address = '127.0.0.1'
    lineage_name = 'lineage.test'
    log_path = tmp_path.joinpath('sftp.log')
    ## Setup client
    client_server = mock_fail_client(client_address)
    client_config = client_conn_config_factory(
        address=client_server.address,
        port=client_server.port,
        domains=[lineage_name],
        push_retries=0
    )
    ## Setup Server
    server_config = tmp_server_config(
        client_configs=[client_config],
        push_retries=0,
        push_interval=0,
        log_level='DEBUG',
        sftp_log_level='CRITICAL',
        log_filename=str(log_path),
        sftp_log_filename='/dev/null'
    )
    ## Setup lineage
    # The filename doesn't matter because it will never get far enough to
    #   matter.
    lineage_path = lineage_factory(lineage_name, ['doesnotmatter.pem'])
    ## Setup test
    server = Server(server_config)
    server.sync(str(lineage_path), [lineage_name])
    ## Run test
    server.serve_forever(one_shot=True)
    ## Verify results
    assert 'DEBUG' in log_path.read_text()


def test_sftp_client_logs_to_given_file(
    mock_fail_client: Callable[[...], MockClientTCPServer],
    canned_client_conn_config: dict,
    lineage_factory: Callable[[...], pathlib.Path],
    tmp_server_config: Callable[[...], ServerConfig],
    tmp_path: pathlib.Path
):
    """Verify the `sftp_log_filename` changes where the SFTP client logs."""
    ## Define some variables to avoid magic values
    log_path = tmp_path.joinpath('sftp.log')
    ## Setup Server
    server_config = tmp_server_config(
        client_configs=[canned_client_conn_config],
        push_retries=0,
        push_interval=0,
        log_level='CRITICAL',
        sftp_log_level='ERROR',
        log_filename='/dev/null',
        sftp_log_filename=str(log_path)
    )
    ## Setup lineage
    # The filename doesn't matter because it will never get far enough to
    #   matter.
    lineage_path = lineage_factory(_TEST_LINEAGE_NAME, ['doesnotmatter.pem'])
    ## Setup test
    server = Server(server_config)
    server.sync(str(lineage_path), [_TEST_LINEAGE_NAME])
    ## Run test
    server.serve_forever(one_shot=True)
    ## Verify results
    print(server_config.sftp_log_filename, 'error in\n', log_path.read_text())
    assert 'ERROR' in log_path.read_text()


def test_sftp_client_logs_at_given_level(
    mock_fail_client: Callable[[...], MockClientTCPServer],
    canned_client_conn_config: dict,
    lineage_factory: Callable[[...], pathlib.Path],
    tmp_server_config: Callable[[...], ServerConfig],
    tmp_path: pathlib.Path
):
    """Verify the `sftp_log_level` changes what the SFTP client logs."""
    ## Define some variables to avoid magic values
    log_path = tmp_path.joinpath('sftp.log')
    ## Setup Server
    server_config = tmp_server_config(
        client_configs=[canned_client_conn_config],
        push_retries=0,
        push_interval=0,
        log_level='CRITICAL',
        sftp_log_level='DEBUG',
        log_filename='/dev/null',
        sftp_log_filename=str(log_path)
    )
    ## Setup lineage
    # The filename doesn't matter because it will never get far enough to
    #   matter.
    lineage_path = lineage_factory(_TEST_LINEAGE_NAME, ['doesnotmatter.pem'])
    ## Setup test
    server = Server(server_config)
    server.sync(str(lineage_path), [_TEST_LINEAGE_NAME])
    ## Run test
    server.serve_forever(one_shot=True)
    ## Verify results
    assert 'DEBUG' in log_path.read_text()
