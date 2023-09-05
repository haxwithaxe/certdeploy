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


def test_logs_at_given_level_to_given_file(
    mock_fail_client: Callable[[...], MockClientTCPServer],
    canned_client_conn_config: dict,
    lineage_factory: Callable[[...], pathlib.Path],
    tmp_server_config: Callable[[...], ServerConfig],
    tmp_path: pathlib.Path
):
    """Verify the `log_filename` config changes where the server logs.

    This also exercises the `log_level` config.
    """
    ## Define some variables to avoid magic values
    log_path = tmp_path.joinpath('sftp.log')
    ## Setup Server
    server_config = tmp_server_config(
        client_configs=[canned_client_conn_config],
        push_retries=0,
        push_interval=0,
        log_level='DEBUG',
        log_filename=str(log_path),
        sftp_log_level='CRITICAL',
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
    assert 'DEBUG' in log_path.read_text()


def test_sftp_client_logs_at_given_level_to_given_file(
    mock_fail_client: Callable[[...], MockClientTCPServer],
    canned_client_conn_config: dict,
    lineage_factory: Callable[[...], pathlib.Path],
    tmp_server_config: Callable[[...], ServerConfig],
    tmp_path: pathlib.Path
):
    """Verify the `sftp_log_filename` changes where the SFTP client logs.

    This also exercises the `sftp_log_level` config.
    """
    ## Define some variables to avoid magic values
    log_path = tmp_path.joinpath('sftp.log')
    ## Setup Server
    server_config = tmp_server_config(
        client_configs=[canned_client_conn_config],
        push_retries=0,
        push_interval=0,
        log_level='CRITICAL',
        log_filename='/dev/null',
        sftp_log_level='DEBUG',
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
