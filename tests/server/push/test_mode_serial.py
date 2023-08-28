"""Tests for the `retry_mode` configs set to 'serial'."""

from certdeploy.server.config.server import PushMode
from certdeploy.server.server import Server

MAX_SECONDS_OFF = 1


def test_push_mode_serial_pushes_one_at_a_time(
        mock_fail_client: callable,
        tmp_server_config: callable,
        client_conn_config_factory: callable,
        lineage_factory: callable
):
    """Verify that the `push_mode` server config set to `serial` pushes to
    clients one at a time.
    """
    ## Define some reused variables
    push_retry_count = 0
    total_push_attempts = 1  # Per client
    # Just to get some definite distance between times
    push_interval = MAX_SECONDS_OFF + 3
    client_address = '127.0.0.1'
    lineage_name = 'lineage.test'
    # The filename doesn't matter because it will never get far enough to
    #   matter.
    lineage_path = str(lineage_factory(lineage_name, ['doesnotmatter.pem']))
    ## Setup client0
    client_server0 = mock_fail_client(client_address)
    client_config0 = client_conn_config_factory(
        address=client_server0.address,
        port=client_server0.port,
        domains=[lineage_name],
        push_retries=push_retry_count
    )
    ## Setup client1
    client_server1 = mock_fail_client(client_address)
    client_config1 = client_conn_config_factory(
        address=client_server1.address,
        port=client_server1.port,
        domains=[lineage_name],
        push_retries=push_retry_count
    )
    ## Setup Server
    server_config = tmp_server_config(
        client_configs=[client_config0, client_config1],
        push_retries=push_retry_count,
        push_interval=push_interval,
        push_mode=PushMode.SERIAL.value
    )
    ## Make something to test
    server = Server(server_config)
    server.sync(lineage_path, [lineage_name])
    server.serve_forever(one_shot=True)
    ## Collect the results
    client0_access_log = client_server0.log
    client1_access_log = client_server1.log
    ## Verify results
    # The log accounts for the first attempt as well as subsequent attempts
    assert len(client0_access_log) == total_push_attempts
    assert len(client1_access_log) == total_push_attempts
    # Now that we know the length is enough get the time difference
    time_diff = client1_access_log[0] - client0_access_log[0]
    # The interval is less than the maximum number of seconds
    assert time_diff.seconds <= push_interval + MAX_SECONDS_OFF
    # The interval is greater than or equal to the nominal interval
    assert time_diff.seconds >= push_interval
