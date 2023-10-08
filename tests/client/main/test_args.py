"""Verify the behavior of the command line options."""

import logging
import pathlib
from typing import Callable

import pytest
from fixtures.logging import ClientRefLogMessages as RefMsgs
from fixtures.logging import ParamikoRefLogMessages as ParamikoMsgs
from fixtures.mock_server import MockPushContext
from fixtures.threading import CleanThread
from fixtures.utils import ConfigContext, KillSwitch
from typer.testing import CliRunner

from certdeploy import PARAMIKO_LOGGER_NAME, LogLevel
from certdeploy.client import log
from certdeploy.client._main import _app
from certdeploy.client.daemon import DeployServer


def test_help_shows_help():
    """Verify that help text is shown for the `--help` arg."""
    ## Run the test
    results = CliRunner(mix_stderr=True).invoke(_app, ['--help'])
    ## Verify the results
    assert results.exception is None
    # The command name is different when it's being called from the runner
    assert RefMsgs.HELP_TEXT_ALT.message in results.output


@pytest.mark.slow
def test_daemon_runs_daemon(
    managed_thread: Callable[[...], CleanThread],
    tmp_client_config_file: Callable[[...], ConfigContext],
    tmp_path: pathlib.Path,
):
    """Verify that the daemon runs for the `--daemon` arg.

    This also covers the `--config` option loading the given config file.
    """
    client_log = tmp_path.joinpath('client.log')
    context = tmp_client_config_file(
        fail_fast=True,
        update_services=[{'type': 'script', 'name': '/usr/bin/true'}],
        sftpd=dict(listen_address='127.0.0.1'),
        log_level='DEBUG',
        log_filename=str(client_log),
    )
    kill_switch = KillSwitch()
    DeployServer._stop_running = kill_switch
    ## Run the test
    thread = managed_thread(
        CliRunner(mix_stderr=True).invoke,
        args=[_app, ['--daemon', '--config', context.config_path]],
        kill_switch=kill_switch,
        teardown=kill_switch.teardown(DeployServer),
    )
    assert thread.is_alive(), 'The client died too soon.'
    # Wait for the magic string to show up in the log
    thread.wait_for_text_in_log(
        RefMsgs.HAS_STARTED.log,
        lambda _: client_log.read_bytes() if client_log.exists() else [],
    )
    thread.reraise_unexpected()
    ## Verify the results
    assert RefMsgs.HAS_STARTED.log in client_log.read_bytes()


def test_no_args_runs_deploy(
    log_file: pathlib.Path,
    managed_thread: Callable[[...], CleanThread],
    tmp_client_config_file: Callable[[...], ConfigContext],
):
    """Verify that the client deploys when no args are given.

    This also covers the `--config` option loading the given config file.
    """
    context = tmp_client_config_file(
        fail_fast=True,
        update_services=[{'type': 'script', 'name': '/usr/bin/true'}],
        sftpd=None,
        log_level='DEBUG',
        log_filename=str(log_file),
    )
    ## Run the test
    results = CliRunner(mix_stderr=True).invoke(
        _app,
        ['--config', context.config_path],
    )
    ## Verify the results
    assert results.exception is None
    # String taken from certdeploy.client.deploy
    assert RefMsgs.DEPLOY_ONLY.log in log_file.read_bytes()


def test_overrides_log_level_and_log_filename(
    tmp_client_config_file: Callable[[...], ConfigContext],
    tmp_path: pathlib.Path,
):
    """Verify that the client log level and log file are overridden.

    This also covers the `--config` option loading the given config file.
    """
    final_log_filename = tmp_path.joinpath('final.log')
    final_log_level = LogLevel.DEBUG
    context = tmp_client_config_file(
        fail_fast=True,
        update_services=[{'type': 'script', 'name': '/usr/bin/true'}],
        sftpd=None,
        log_level='CRITICAL',
        log_filename=str(tmp_path.joinpath('initial.log')),
    )
    ## Run the test
    results = CliRunner(mix_stderr=True).invoke(
        _app,
        [
            '--log-level',
            final_log_level.value,
            '--log-filename',
            str(final_log_filename),
            '--config',
            context.config_path,
        ],
    )
    ## Verify the results
    assert results.exception is None
    assert LogLevel.cast(log.level) == final_log_level
    assert log.handlers[0].stream.name == str(final_log_filename)


@pytest.mark.slow
def test_overrides_sftp_log_level_and_sftp_log_filename(
    managed_thread: Callable[[...], CleanThread],
    mock_server_push: Callable[[...], MockPushContext],
    tmp_client_config_file: Callable[[...], ConfigContext],
    tmp_path: pathlib.Path,
):
    """Verify that the client log level and log file are overridden.

    This also covers the `--config` option loading the given config file.
    """
    client_log = tmp_path.joinpath('client.log')
    final_log_path = tmp_path.joinpath('final.log')
    final_log_level = LogLevel.DEBUG
    context = tmp_client_config_file(
        tmp_path=tmp_path,
        fail_fast=True,
        update_services=[{'type': 'script', 'name': '/usr/bin/true'}],
        log_level=LogLevel.DEBUG.value,
        log_filename=str(client_log),
        sftpd=dict(
            log_level='CRITICAL',
            log_filename=str(tmp_path.joinpath('initial.log')),
        ),
    )
    mock_server = mock_server_push(client_context=context)
    kill_switch = KillSwitch()
    DeployServer._stop_running = kill_switch
    ## Run the test
    thread = managed_thread(
        CliRunner(mix_stderr=True).invoke,
        args=[
            _app,
            [
                '--daemon',
                '--sftp-log-level',
                final_log_level.value,
                '--sftp-log-filename',
                str(final_log_path),
                '--config',
                str(context.config_path),
            ],
        ],
        kill_switch=kill_switch,
        teardown=kill_switch.teardown(DeployServer),
    )
    thread.wait_for_text_in_log(
        RefMsgs.HAS_STARTED.log, lambda x: client_log.read_bytes()
    )
    assert thread.is_alive(), 'The client died too soon.'
    mock_server.push()
    thread.wait_for_text_in_log(
        ParamikoMsgs.TRANSPORT_EMPTY.log, lambda x: final_log_path.read_bytes()
    )
    thread.reraise_unexpected()
    ## Verify the result
    assert ParamikoMsgs.TRANSPORT_EMPTY.log in final_log_path.read_bytes()
    paramiko_log = logging.getLogger(name=PARAMIKO_LOGGER_NAME)
    assert LogLevel.cast(paramiko_log.getEffectiveLevel()) == final_log_level
    assert paramiko_log.handlers[0].stream.name == str(final_log_path)
