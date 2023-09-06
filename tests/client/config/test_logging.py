"""Check that the various logging configs do what they say they do."""

import pathlib
from typing import Callable

import paramiko
from fixtures.threading import CleanThread

from certdeploy.client.config import ClientConfig
from certdeploy.client.daemon import DeployServer


def test_logs_at_given_level_to_given_file(
    simple_thread: Callable[[...], CleanThread],
    wait_for_condition: Callable[[Callable[[], bool], int], None],
    tmp_client_config: Callable[[...], ClientConfig],
    tmp_path: pathlib.Path
):
    """Verify the `log_filename` config changes where the server logs.

    This also exercises the `log_level` config.
    """
    ## Define some variables to avoid magic values
    log_path = tmp_path.joinpath('test.log')
    ## Setup client
    client_config = tmp_client_config(
        log_level='DEBUG',
        log_filename=str(log_path),
        sftpd=dict(
            listen_address='127.0.0.1',
            log_level='CRITICAL',
            log_filename='/dev/null'
        )
    )
    ## Setup test
    client = DeployServer(client_config)

    client_thread = simple_thread(
        client.serve_forever,
        allowed_exceptions=[paramiko.ssh_exception.SSHException],
        kill_switch=client._stop_running
    )
    ## Run test
    client_thread.start()
    wait_for_condition((lambda: 'DEBUG' in log_path.read_text()), 300)
    client_thread.stop()
    ## Formally verify results
    assert 'DEBUG' in log_path.read_text()


def test_sftpd_logs_at_given_level_to_given_file(
    simple_thread: Callable[[...], CleanThread],
    socket_poker: Callable[[str, int, str], None],
    wait_for_condition: Callable[[Callable[[], bool], int], None],
    tmp_client_config: Callable[[...], ClientConfig],
    tmp_path: pathlib.Path
):
    """Verify the `log_filename` config changes where the server logs.

    This also exercises the `log_level` config.
    """
    ## Define some variables to avoid magic values
    log_path = tmp_path.joinpath('test.log')
    ## Setup client
    client_config = tmp_client_config(
        log_level='CRITICAL',
        log_filename='/dev/null',
        sftpd=dict(
            listen_address='127.0.0.1',
            log_level='DEBUG',
            log_filename=str(log_path)
        )
    )
    ## Setup test
    client = DeployServer(client_config)
    client_thread = simple_thread(
        client.serve_forever,
        allowed_exceptions=[paramiko.ssh_exception.SSHException],
        kill_switch=client._stop_running
    )
    client_thread.start()
    ## Run test
    # Connect to the client to generate some paramiko log traffic
    socket_poker(client_config.sftpd_config.listen_address,
                 client_config.sftpd_config.listen_port,
                 'Just testing logging')
    # Wait for the logs to have what we want
    wait_for_condition((lambda: 'DEBUG' in log_path.read_text()), 300)
    ## Clean up
    client_thread.stop()
    ## Formally verify results
    assert 'DEBUG' in log_path.read_text()
