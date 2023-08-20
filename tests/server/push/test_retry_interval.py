"""Tests for the `push_retry_interval` configs.

Both the server and client connection configs.
"""

from certdeploy.server.config import ServerConfig
from certdeploy.server.server import Server

MAX_SECONDS_OFF = 1


def test_retries_on_server_interval_is_timely(
        mock_fail_client: callable,
        tmp_server_config: callable,
        client_conn_config_factory: callable,
        lineage_factory: callable
):
    """Verify that the `retry_interval` server config produces retries on an
    interval.
    """
    ## Define some reused variables
    push_retry_count = 1
    total_push_attempts = push_retry_count + 1
    push_retry_interval = 3
    client_address = '127.0.0.1'
    lineage_name = 'lineage.test'
    # The filename doesn't matter because it will never get far enough to
    #   matter.
    lineage_path = str(lineage_factory(lineage_name, ['doesnotmatter.pem']))
    ## Setup client
    client_server = mock_fail_client(client_address)
    client_config = client_conn_config_factory(
        address=client_server.address,
        port=client_server.port,
        domains=[lineage_name]
    )
    ## Setup server
    server_config_filename, _ = tmp_server_config(
        client_configs=[client_config],
        push_retries=push_retry_count,
        push_retry_interval=push_retry_interval,
    )
    server_config = ServerConfig.load(server_config_filename)
    ## Make something to test
    server = Server(server_config)
    server.sync(lineage_path, [lineage_name])
    server.serve_forever(one_shot=True)
    ## Collect results
    client_access_log = client_server.log
    ## Verify results
    # The log accounts for the first attempt as well as subsequent attempts
    assert len(client_access_log) == total_push_attempts
    # Now that we know the length is enough get the time difference
    time_diff = client_access_log[1] - client_access_log[0]
    # The interval is less than the maximum number of seconds
    assert time_diff.seconds <= push_retry_interval+MAX_SECONDS_OFF
    # The interval is greater than or equal to the nominal interval
    assert time_diff.seconds >= push_retry_interval


def test_retries_on_client_interval_is_timely(
        mock_fail_client: callable,
        tmp_server_config: callable,
        client_conn_config_factory: callable,
        lineage_factory: callable
):
    """Verify that the `retry_interval` client config produces retries on that
    interval and overrides the server config.
    """
    ## Define some reused variables
    push_retry_count = 1
    total_push_attempts = push_retry_count + 1
    client_push_retry_interval = 3
    push_retry_interval = client_push_retry_interval + MAX_SECONDS_OFF + 2
    client_address = '127.0.0.1'
    lineage_name = 'lineage.test'
    # The filename doesn't matter because it will never get far enough to
    #   matter.
    lineage_path = str(lineage_factory(lineage_name, ['doesnotmatter.pem']))
    ## Setup client
    client_server = mock_fail_client(client_address)
    client_config = client_conn_config_factory(
        address=client_server.address,
        port=client_server.port,
        domains=[lineage_name],
        push_retry_interval=client_push_retry_interval
    )
    ## Setup server
    server_config_filename, _ = tmp_server_config(
        client_configs=[client_config],
        push_retries=push_retry_count,
        push_retry_interval=push_retry_interval,
    )
    server_config = ServerConfig.load(server_config_filename)
    ## Make something to test
    server = Server(server_config)
    server.sync(lineage_path, [lineage_name])
    server.serve_forever(one_shot=True)
    ## Collect results
    client_access_log = client_server.log
    ## Verify results
    # The log accounts for the first attempt as well as subsequent attempts
    assert len(client_access_log) == total_push_attempts
    # Now that we know the length is enough get the time difference
    time_diff = client_access_log[1] - client_access_log[0]
    # The interval is less than or equal to the maximum number of seconds
    assert time_diff.seconds <= client_push_retry_interval+MAX_SECONDS_OFF
    # The interval is greater than or equal to the nominal interval
    assert time_diff.seconds >= client_push_retry_interval