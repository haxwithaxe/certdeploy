"""Tests for the `push_interval` config."""

from certdeploy.server.server import Server

MAX_SECONDS_OFF = 1


def test_tries_on_interval(
        mock_fail_client: callable,
        tmp_server_config: callable,
        client_conn_config_factory: callable,
        lineage_factory: callable
):
    """Verify that the `push_interval` tries on an interval."""
    ## Define some variables to avoid magic values
    push_interval = 1
    push_retry_count = 0
    total_push_attempts = 1
    client_address = '127.0.0.1'
    lineage_name = 'lineage.test'
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
        push_retries=push_retry_count,
        push_interval=push_interval
    )
    ## Setup lineage
    # The filename doesn't matter because it will never get far enough to
    #   matter.
    lineage_path = str(lineage_factory(lineage_name, ['doesnotmatter.pem']))
    ## Setup test
    server = Server(server_config)
    server.sync(lineage_path, [lineage_name])
    ## Run test
    server.serve_forever(one_shot=True)
    ## Collect results
    client0_access_log = client0_server.log
    client1_access_log = client1_server.log
    ## Verify results
    # The log accounts for the first attempt as well as subsequent attempts
    assert len(client0_access_log) == total_push_attempts
    assert len(client1_access_log) == total_push_attempts
    # Now that we know the length is enough get the time difference
    time_diff = client1_access_log[0] - client0_access_log[0]
    # The interval is less than the maximum number of seconds
    assert time_diff.seconds <= push_interval+MAX_SECONDS_OFF
    # The interval is greater than or equal to the nominal interval
    assert time_diff.seconds >= push_interval
