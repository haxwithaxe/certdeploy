"""Verify the behavior of the command line options.

These tests only run the server long enough to see that it's going down the
right code path. These are not end to end tests.
"""

import logging
import os
import pathlib
from typing import Callable

import pytest
from fixtures.logging import ServerRefLogMessages as RefMsgs
from fixtures.threading import CleanThread
from fixtures.utils import ConfigContext, KillSwitch
from typer.testing import CliRunner

from certdeploy import DEFAULT_SERVER_CONFIG, PARAMIKO_LOGGER_NAME, LogLevel
from certdeploy.server import log
from certdeploy.server._main import _app
from certdeploy.server.server import Server


def test_help_shows_help():
    """Verify that help text is shown for the `--help` arg."""
    ## Run the test
    result = CliRunner(mix_stderr=True).invoke(_app, ['--help'])
    ## Verify the results
    # The command name is different when it's being called from the runner
    assert RefMsgs.HELP_TEXT_ALT.message in result.output


def test_daemon_runs_daemon(
    log_file: pathlib.Path,
    managed_thread: Callable[[...], CleanThread],
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify that the daemon runs for the `--daemon` arg.

    This also covers the `--config` option loading the given config file.
    """
    # String taken from certdeploy.client.daemon.DeployServer.serve_forever
    # The `False` is the expected value of `one_shot` given it's daemon mode
    context = tmp_server_config_file(
        fail_fast=True,
        log_level='DEBUG',
        log_filename=str(log_file)
    )
    kill_switch = KillSwitch()
    Server._stop_running = kill_switch
    ## Run the test
    thread = managed_thread(
        CliRunner(mix_stderr=True).invoke,
        args=[_app, ['--daemon', '--config', context.config_path]],
        kill_switch=kill_switch,
        teardown=kill_switch.teardown(Server)
    )
    # Wait for the magic string to show up in the log
    thread.wait_for_text_in_log(RefMsgs.DAEMON_HAS_STARTED.log,
                                lambda x: log_file.read_bytes())
    thread.reraise_unexpected()
    ## Verify the results
    assert RefMsgs.DAEMON_HAS_STARTED.log in log_file.read_bytes()


@pytest.mark.slow
def test_renew_runs_renew(
    log_file: pathlib.Path,
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify that renew runs for the `--renew` arg.

    This also covers the `--config` option loading the given config file.
    """
    context = tmp_server_config_file(
        renew_exec='/usr/bin/true',
        fail_fast=True,
        log_level='DEBUG',
        log_filename=str(log_file)
    )
    ## Run the test
    results = CliRunner(mix_stderr=True).invoke(
        _app,
        ['--renew', '--config', context.config_path]
    )
    ## Verify the results
    assert results.exception is None
    assert RefMsgs.RENEW_ONLY.log in log_file.read_bytes()


def test_push_runs_push(
    log_file: pathlib.Path,
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify that the daemon runs for the `--daemon` arg.

    This also covers the `--config` option loading the given config file.
    """
    context = tmp_server_config_file(
        fail_fast=True,
        log_level='DEBUG',
        log_filename=str(log_file)
    )
    ## Run the test
    results = CliRunner(mix_stderr=True).invoke(
        _app,
        ['--push', '--config', context.config_path]
    )
    ## Verify the results
    assert results.exception is None
    assert RefMsgs.PUSH_HAS_STARTED.log in log_file.read_bytes()


def test_no_args_with_config_exits(
    log_file: pathlib.Path,
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify the server errors out when no args besides `--config` are given.

    This also covers the `--config` option loading the given config file.
    """
    # String taken from certdeploy.server._main
    context = tmp_server_config_file(
        fail_fast=True,
        log_level='DEBUG',
        log_filename=str(log_file)
    )
    ## Run the test
    results = CliRunner(mix_stderr=True).invoke(
        _app,
        ['--config', context.config_path]
    )
    ## Verify the results
    assert isinstance(results.exception, SystemExit)
    assert results.exception.code == 1
    assert RefMsgs.MISSING_LINEAGE.log in log_file.read_bytes()


@pytest.mark.real
def test_no_args_exits(
    caplog: pytest.LogCaptureFixture,
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify that the server errors out when no args are given.

    This also covers the `--config` option loading the given config file.

    This test uses `caplog` because the error doesn't show up in the
    `results.output`. It shows up in stdout or stderr when run manually.
    """
    assert not os.path.exists(DEFAULT_SERVER_CONFIG), \
        (f'The default server config ({DEFAULT_SERVER_CONFIG}) exists. This '
         'tests requires that it not exist.')
    ## Run the test
    results = CliRunner(mix_stderr=True).invoke(_app, [])
    ## Verify the results
    assert isinstance(results.exception, SystemExit)
    assert results.exception.code == 1
    assert RefMsgs.MISSING_CONFIG.message in caplog.messages


def test_overrides_log_level_and_log_filename(
    log_file: pathlib.Path,
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify that the client log level and log file are overridden.

    This also covers the `--config` option loading the given config file.
    """
    final_log_level = LogLevel.DEBUG
    context = tmp_server_config_file(
        fail_fast=True,
        log_level='CRITICAL',
        log_filename='/dev/null'
    )
    ## Run the test
    results = CliRunner(mix_stderr=True).invoke(
        _app,
        [
            '--push',
            '--log-level', final_log_level.value,
            '--log-filename', str(log_file),
            '--config', context.config_path
        ]
    )
    ## Verify the results
    # If an exception occurred the test failed
    assert results.exception is None
    # At least one DEBUG message was sent
    assert RefMsgs.PUSH_ONLY.log in log_file.read_bytes()
    assert LogLevel.cast(log.level) == final_log_level
    assert log.handlers[0].stream.name == str(log_file)


def test_overrides_sftp_log_level_and_sftp_log_filename(
    log_file: pathlib.Path,
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify that the client log level and log file are overridden.

    This also covers the `--config` option loading the given config file.
    """
    final_log_level = LogLevel.DEBUG
    context = tmp_server_config_file(
        fail_fast=True,
        sftp_log_level='CRITICAL',
        sftp_log_filename='/dev/null'
    )
    ## Run the test
    results = CliRunner(mix_stderr=True).invoke(
        _app,
        [
            '--push',
            '--sftp-log-level', final_log_level.value,
            '--sftp-log-filename', str(log_file),
            '--config', context.config_path
        ]
    )
    ## Verify the results
    assert results.exception is None
    # No paramiko logs are expected to be generated in this code path
    paramiko_log = logging.getLogger(name=PARAMIKO_LOGGER_NAME)
    assert LogLevel.cast(paramiko_log.getEffectiveLevel()) == final_log_level
    assert paramiko_log.handlers[0].stream.name == str(log_file)


def test_push_lineage_and_domains_queues_and_pushes(
    log_file: pathlib.Path,
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify that the server queues and pushes.

    The server must both queue and push when given `--push`, `--lineage`, and
    `--domain` arguments.

    This also covers the `--config` option loading the given config file.
    """
    # In order for this to run without trying to actually push the
    #   domain/lineage needs to not be 'test.example.com' or whatever the
    #   default one in the `tmp_server_config_file` currently is.
    lineage_domain = 'dont.match'
    context = tmp_server_config_file(
        fail_fast=True,
        log_level='DEBUG',
        log_filename=str(log_file)
    )
    for client in context.config['client_configs']:
        assert lineage_domain not in client['domains'], \
            '`lineage_domain` must not match configured client domains'
    ## Run the test
    results = CliRunner(mix_stderr=True).invoke(
        _app,
        args=['--push',
              '--lineage', lineage_domain,
              '--domains', lineage_domain,
              '--config', context.config_path]
    )
    ## Verify the results
    assert results.exception is None
    assert RefMsgs.ADD_TO_QUEUE_MESSAGE.log in log_file.read_bytes()
    assert RefMsgs.PUSH_ONLY.log in log_file.read_bytes()
