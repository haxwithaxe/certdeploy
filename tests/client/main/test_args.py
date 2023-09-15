"""Verify the behavior of the command line options."""

import logging
import pathlib
from typing import Callable

import pytest
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
    assert 'Usage: -typer-main [OPTIONS]' in results.output


def test_daemon_runs_daemon(
    managed_thread: Callable[[...], CleanThread],
    tmp_client_config_file: Callable[[...], ConfigContext],
    tmp_path: pathlib.Path
):
    """Verify that the daemon runs for the `--daemon` arg.

    This also covers the `--config` option loading the given config file.
    """
    client_log = tmp_path.joinpath('client.log')
    client_log.write_text('')
    # String taken from certdeploy.client.daemon.DeployServer.serve_forever
    trigger = 'Listening for incoming connections at '
    context = tmp_client_config_file(
        fail_fast=True,
        update_services=[{'type': 'script', 'name': '/usr/bin/true'}],
        sftpd=dict(listen_address='127.0.0.1'),
        log_level='DEBUG',
        log_filename=str(client_log)
    )
    kill_switch = KillSwitch()
    DeployServer._stop_running = kill_switch
    ## Run the test
    thread = managed_thread(
        CliRunner(mix_stderr=True).invoke,
        args=[_app, ['--daemon', '--config', context.config_path]],
        kill_switch=kill_switch,
        teardown=kill_switch.teardown(DeployServer),
        reraise=True
    )
    assert thread.is_alive()
    # Wait for the magic string to show up in the log
    thread.wait_for_text_in_log(trigger, lambda _: client_log.read_text())
    thread.reraise_unexpected()
    ## Verify the results
    assert trigger in client_log.read_text()


def test_no_args_runs_deploy(
    managed_thread: Callable[[...], CleanThread],
    tmp_client_config_file: Callable[[...], ConfigContext],
    caplog: pytest.LogCaptureFixture
):
    """Verify that the client deploys when no args are given.

    This also covers the `--config` option loading the given config file.
    """
    context = tmp_client_config_file(
        fail_fast=True,
        update_services=[{'type': 'script', 'name': '/usr/bin/true'}],
        sftpd=None,
        log_level='DEBUG'
    )
    ## Run the test
    results = CliRunner(mix_stderr=True).invoke(
        _app,
        ['--config', context.config_path]
    )
    ## Verify the results
    assert results.exception is None
    # String taken from certdeploy.client.deploy
    assert 'Running one off deploy' in caplog.messages


def test_overrides_log_level_and_log_filename(
    tmp_client_config_file: Callable[[...], ConfigContext],
    tmp_path: pathlib.Path
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
        log_filename=str(tmp_path.joinpath('initial.log'))
    )
    ## Run the test
    results = CliRunner(mix_stderr=True).invoke(
        _app,
        ['--log-level', final_log_level.value,
         '--log-filename', str(final_log_filename),
         '--config', context.config_path]
    )
    ## Verify the results
    assert results.exception is None
    assert LogLevel.cast(log.level) == final_log_level
    assert log.handlers[0].stream.name == str(final_log_filename)


def test_overrides_sftp_log_level_and_sftp_log_filename(
    managed_thread: Callable[[...], CleanThread],
    tmp_client_config_file: Callable[[...], ConfigContext],
    tmp_path: pathlib.Path
):
    """Verify that the client log level and log file are overridden.

    This also covers the `--config` option loading the given config file.
    """
    # String taken from certdeploy.client.deploy
    final_log_filename = tmp_path.joinpath('final.log')
    final_log_level = LogLevel.DEBUG
    context = tmp_client_config_file(
        fail_fast=True,
        update_services=[{'type': 'script', 'name': '/usr/bin/true'}],
        sftpd=dict(
            log_level='CRITICAL',
            log_filename=str(tmp_path.joinpath('initial.log'))
        )
    )
    kill_switch = KillSwitch()
    DeployServer._stop_running = kill_switch
    ## Run the test
    thread = managed_thread(
        CliRunner(mix_stderr=True).invoke,
        args=[
            _app,
            ['--sftp-log-level', final_log_level.value,
             '--sftp-log-filename', final_log_filename,
             '--config', context.config_path]
        ],
        kill_switch=kill_switch,
        teardown=kill_switch.teardown(DeployServer)
    )
    ## Verify the results
    thread.wait_for_text_in_log(
        (PARAMIKO_LOGGER_NAME, int(LogLevel.DEBUG)),
        lambda x: [(r[0], r[1]) for r in x.caplog.record_tuples]
    )
    thread.reraise_unexpected()
    paramiko_log = logging.getLogger(name=PARAMIKO_LOGGER_NAME)
    assert LogLevel.cast(paramiko_log.getEffectiveLevel()) == final_log_level
    assert paramiko_log.handlers[0].stream.name == str(final_log_filename)
