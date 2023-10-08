"""Check that the various logging configs do what they say they do."""

import logging
import pathlib
from typing import Callable

import paramiko
from fixtures.keys import KeyPair
from fixtures.logging import ClientRefLogMessage
from fixtures.logging import ClientRefLogMessages as RefMsgs
from fixtures.logging import ParamikoRefLogMessages as ParamikoRefMsgs
from fixtures.mock_server import MockPushContext
from fixtures.threading import CleanThread, KillSwitch

from certdeploy import PARAMIKO_LOGGER_NAME, LogLevel
from certdeploy.client import log
from certdeploy.client.config import ClientConfig
from certdeploy.client.daemon import DeployServer


def test_logs_at_given_level_to_given_file(
    managed_thread: Callable[[...], CleanThread],
    wait_for_condition: Callable[[Callable[[], bool], int], None],
    tmp_client_config: Callable[[...], ClientConfig],
    tmp_path: pathlib.Path,
):
    """Verify the `log_filename` config changes where the server logs.

    This also exercises the `log_level` config.
    """
    ## Define some variables to avoid magic values
    log_level = LogLevel.DEBUG
    log_path = tmp_path.joinpath('test.log')
    ## Setup client
    client_config = tmp_client_config(
        log_level=log_level.value,
        log_filename=str(log_path),
        sftpd=dict(
            listen_address='127.0.0.1',
            log_level='CRITICAL',
            log_filename='/dev/null',
        ),
    )
    ## Setup test
    kill_switch = KillSwitch()
    client = DeployServer(client_config)
    client._stop_running = kill_switch
    ## Run test
    client_thread = managed_thread(
        client.serve_forever,
        allowed_exceptions=[paramiko.ssh_exception.SSHException],
        kill_switch=kill_switch,
        teardown=kill_switch.teardown(client),
    )
    client_thread.wait_for_text_in_log(
        RefMsgs.HAS_STARTED.log, lambda _: log_path.read_bytes()
    )
    client_thread.reraise_unexpected()
    ## Formally verify results
    assert (
        ClientRefLogMessage(log_level.value, '', 'made up here').log
        in log_path.read_bytes()
    )
    assert LogLevel.cast(log.level) == log_level
    assert log.handlers[0].stream.name == str(log_path)


def test_sftpd_logs_at_given_level_to_given_file(
    managed_thread: Callable[[...], CleanThread],
    wait_for_condition: Callable[[Callable[[], bool], int], None],
    keypairgen: Callable[[...], KeyPair],
    mock_server_push: Callable[[...], MockPushContext],
    tmp_client_config: Callable[[...], ClientConfig],
    tmp_path: pathlib.Path,
):
    """Verify the `log_filename` config changes where the server logs.

    This also exercises the `log_level` config.
    """
    ## Define some variables to avoid magic values
    client_log_path = tmp_path.joinpath('client.log')
    listen_address = '127.0.0.1'
    log_level = LogLevel.DEBUG
    log_path = tmp_path.joinpath('paramiko.log')
    ## Setup client
    tester_keypair = keypairgen()
    tester_keypair.update(tmp_path, 'tester_key')
    client_keypair = keypairgen()
    client_keypair.update(tmp_path, 'client_key')
    client_config = tmp_client_config(
        tmp_path=tmp_path,
        client_keypair=client_keypair,
        server_keypair=tester_keypair,
        log_level='DEBUG',
        log_filename=str(client_log_path),
        sftpd=dict(
            listen_address=listen_address,
            log_level=log_level.value,
            log_filename=str(log_path),
            server_pubkey=tester_keypair.pubkey_text,
        ),
    )
    ## Setup test
    mock_server = mock_server_push(
        client_config,
        pathlib.Path('staging'),
        client_keypair=client_keypair,
        server_keypair=tester_keypair,
    )
    kill_switch = KillSwitch()
    client = DeployServer(client_config)
    client._stop_running = kill_switch
    client_thread = managed_thread(
        client.serve_forever,
        allowed_exceptions=[paramiko.ssh_exception.SSHException],
        kill_switch=kill_switch,
        teardown=kill_switch.teardown(client),
    )
    client_thread.wait_for_text_in_log(
        RefMsgs.HAS_STARTED.log, lambda x: client_log_path.read_bytes()
    )
    assert (
        client_thread.is_alive() is True
    ), f'Client is dead too soon: {client_thread.caplog.messages[-1]}'
    ## Run test
    # Connect to the client to generate some paramiko log traffic
    mock_server.push()
    ## Verify results
    client_thread.reraise_unexpected()
    paramiko_log = logging.getLogger(name=PARAMIKO_LOGGER_NAME)
    assert LogLevel.cast(paramiko_log.getEffectiveLevel()) == log_level
    assert paramiko_log.handlers[0].stream.name == str(log_path)
    assert ParamikoRefMsgs.TRANSPORT_EMPTY.log in log_path.read_bytes()
    assert ParamikoRefMsgs.TRANSPORT_SFTP_EMPTY.log in log_path.read_bytes()
