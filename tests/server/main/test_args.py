"""Verify the behavior of the command line options.

These tests only run the server long enough to see that it's going down the
right code path. These are not end to end tests.
"""

import logging
import os
import pathlib
from typing import Callable

import pytest
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
    assert 'Usage: -typer-main [OPTIONS]' in result.output


def test_daemon_runs_daemon(
    managed_thread: Callable[[...], CleanThread],
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify that the daemon runs for the `--daemon` arg.

    This also covers the `--config` option loading the given config file.
    """
    # String taken from certdeploy.client.daemon.DeployServer.serve_forever
    # The `False` is the expected value of `one_shot` given it's daemon mode
    trigger = 'Server.serve_forever: one_shot=False'
    context = tmp_server_config_file(
        fail_fast=True,
        log_level='DEBUG'
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
    thread.wait_for_text_in_log(trigger, lambda x: x.caplog.text)
    thread.reraise_unexpected()
    ## Verify the results
    assert trigger in thread.caplog.text


def test_renew_runs_renew(
    tmp_server_config_file: Callable[[...], ConfigContext],
    caplog: pytest.LogCaptureFixture
):
    """Verify that renew runs for the `--renew` arg.

    This also covers the `--config` option loading the given config file.
    """
    context = tmp_server_config_file(
        renew_exec='/usr/bin/true',
        fail_fast=True,
        log_level='DEBUG'
    )
    ## Run the test
    results = CliRunner(mix_stderr=True).invoke(
        _app,
        ['--renew', '--config', context.config_path]
    )
    ## Verify the results
    assert results.exception is None
    # String taken from certdeploy.server._main._run
    assert 'Running renew' in caplog.messages


def test_push_runs_push(
    tmp_server_config_file: Callable[[...], ConfigContext],
    caplog: pytest.LogCaptureFixture
):
    """Verify that the daemon runs for the `--daemon` arg.

    This also covers the `--config` option loading the given config file.
    """
    context = tmp_server_config_file(
        fail_fast=True,
        log_level='DEBUG'
    )
    ## Run the test
    results = CliRunner(mix_stderr=True).invoke(
        _app,
        ['--push', '--config', context.config_path]
    )
    ## Verify the results
    assert results.exception is None
    # String taken from certdeploy.server.server.Server.serve_forever
    # The `True` is the expected value of `one_shot` given it's push mode
    assert 'Server.serve_forever: one_shot=True' in caplog.messages


def test_no_args_with_config_exits(
    tmp_server_config_file: Callable[[...], ConfigContext],
    caplog: pytest.LogCaptureFixture
):
    """Verify the server errors out when no args besides `--config` are given.

    This also covers the `--config` option loading the given config file.
    """
    # String taken from certdeploy.server._main
    context = tmp_server_config_file(
        fail_fast=True,
        log_level='DEBUG'
    )
    ## Run the test
    results = CliRunner(mix_stderr=True).invoke(
        _app,
        ['--config', context.config_path]
    )
    ## Verify the results
    assert isinstance(results.exception, SystemExit)
    assert results.exception.code == 1
    # String taken from certdeploy.server._main._run
    assert 'Could not find lineage or domains.' in caplog.text


def test_no_args_exits(
    tmp_server_config_file: Callable[[...], ConfigContext],
    caplog: pytest.LogCaptureFixture
):
    """Verify that the server errors out when no args are given.

    This also covers the `--config` option loading the given config file.
    """
    assert not os.path.exists(DEFAULT_SERVER_CONFIG), \
        (f'The default server config ({DEFAULT_SERVER_CONFIG}) exists. This '
         'tests requires that it not exist.')
    ## Run the test
    results = CliRunner(mix_stderr=True).invoke(_app, [])
    ## Verify the results
    assert isinstance(results.exception, SystemExit)
    assert results.exception.code == 1
    # String taken from running `certdeploy-server` with no args
    error = ('FileNotFoundError: [Errno 2] No such file or directory: '
             '\'/etc/certdeploy/server.yml\'')
    assert error in caplog.messages


def test_overrides_log_level_and_log_filename(
    tmp_server_config_file: Callable[[...], ConfigContext],
    caplog: pytest.LogCaptureFixture,
    tmp_path: pathlib.Path
):
    """Verify that the client log level and log file are overridden.

    This also covers the `--config` option loading the given config file.
    """
    final_log_filename = tmp_path.joinpath('final.log')
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
            '--log-filename', final_log_filename,
            '--config', context.config_path
        ]
    )
    ## Collect results

    def _test(record):
        return (record[0] == 'certdeploy-server' and
                record[1] == int(LogLevel.DEBUG))

    debug_server_records = [True for x in caplog.record_tuples if _test(x)]
    ## Verify the results
    # If an exception occurred the test failed
    assert results.exception is None
    # At least one DEBUG message was sent
    assert True in debug_server_records
    assert LogLevel.cast(log.level) == final_log_level
    assert log.handlers[0].stream.name == str(final_log_filename)


def test_overrides_sftp_log_level_and_sftp_log_filename(
    tmp_server_config_file: Callable[[...], ConfigContext],
    caplog: pytest.LogCaptureFixture,
    tmp_path: pathlib.Path
):
    """Verify that the client log level and log file are overridden.

    This also covers the `--config` option loading the given config file.
    """
    final_log_filename = tmp_path.joinpath('final.log')
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
            '--sftp-log-filename', final_log_filename,
            '--config', context.config_path
        ]
    )
    ## Verify the results
    assert results.exception is None
    # No paramiko logs are expected to be generated in this code path
    paramiko_log = logging.getLogger(name=PARAMIKO_LOGGER_NAME)
    assert LogLevel.cast(paramiko_log.getEffectiveLevel()) == final_log_level
    assert paramiko_log.handlers[0].stream.name == str(final_log_filename)


def test_push_lineage_and_domains_queues_and_pushes(
    tmp_server_config_file: Callable[[...], ConfigContext],
    caplog: pytest.LogCaptureFixture
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
        log_level='DEBUG'
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
    assert 'Adding lineage to queue.' in caplog.messages
    assert 'Running manual push without a running daemon' in caplog.messages
