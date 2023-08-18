"""Tests for the `retry_interval` configs.

Both the server and client connection configs.
"""

from certdeploy.server.config import ServerConfig
from certdeploy.server.server import Server

MAX_SECONDS_OFF = 1


def test_interval_is_timely(
        mock_fail_client: callable,
        tmp_server_config: callable,
        client_conn_config_factory: callable,
        lineage_factory: callable
):
    """Verify that the `retry_interval` server config produces retries at that
    interval.
    """
    # Define some reused variables
    push_retry_count = 1
    total_push_attempts = push_retry_count + 1
    push_retry_interval = 3
    client_address = '127.0.0.1'
    lineage_name = 'lineage.test'
    # The filename doesn't matter because it will never get far enough to
    #   matter.
    lineage_path = lineage_factory(lineage_name, ['doesnotmatter.pem'])
    # Setup client config
    client_port, client_server = mock_fail_client(client_address)
    client_config = client_conn_config_factory(
        address=client_address,
        port=client_port,
        domains=[lineage_name]
    )
    # Setup Server
    server_config_filename, _ = tmp_server_config(
        client_configs=[client_config],
        push_retries=push_retry_count,
        push_retry_interval=push_retry_interval,
    )
    server_config = ServerConfig.load(server_config_filename)
    # Make something to test
    server = Server(server_config)
    server.sync(str(lineage_path), [lineage_name])
    server.serve_forever(one_shot=True)
    # Verify results
    client_access_log = client_server.log
    # The log accounts for the first attempt as well as subsequent attempts
    assert len(client_access_log) == total_push_attempts
    # Now that we know the length is enough get the time difference
    time_diff = client_access_log[1] - client_access_log[0]
    # The interval is less than the maximum number of seconds
    assert time_diff.seconds <= push_retry_interval+MAX_SECONDS_OFF
    # The interval is greater than or equal to the nominal interval
    assert time_diff.seconds >= push_retry_interval
