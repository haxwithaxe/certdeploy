"""Logging and log message formatting fixtures and utilities."""

import logging
import pathlib

import pytest

from certdeploy import (
    CERTDEPLOY_CLIENT_LOGGER_NAME,
    CERTDEPLOY_SERVER_LOGGER_NAME,
    DEFAULT_LOG_FORMAT,
    PARAMIKO_LOGGER_NAME
)


class _RefLogMessage:
    """Base class for formatted log messages.

    Arguments:
        level: The log level as a string.
        message: The log message.
        source: The source of `message`. This should be the path to the method
            or function (eg `certdeploy.server._main._run`). If it's made up
            for a test the string ``made up`` is appropriate.
        logger_name (optional): The name of the `logging.Logger`. This is just
            for extra custom, one off instances. Defaults to the class's
            defined `_logger_name`.
    """

    _log_format = DEFAULT_LOG_FORMAT
    _logger_name = None

    def __init__(self, level: str, message: str, source: str,
                 logger_name: str = None):
        self._level = level
        self._message = message
        self._source = source
        self._logger_name = logger_name or self._logger_name

    @property
    def level(self) -> str:
        """The log level as a string."""
        return self._level

    @property
    def log(self) -> bytes:
        """The formatted log message."""
        return (self._log_format % dict(
            levelname=self._level,
            name=self._logger_name,
            message=self._message
        )).encode()

    @property
    def message(self) -> str:
        """The message from the log."""
        return self._message

    def __repr__(self) -> str:
        return (
            f'<self.__class__.__name__ '
            f'logger={self._logger_name}, '
            f'level={self._level}, '
            f'message={self._message}, '
            f'source={self._source}, '
            f'log={self.log}'
            '>'
        )


class PlainText(_RefLogMessage):
    """An unformatted message."""

    _log_format: str = '%(message)'
    _logger_name: str = 'Plain text'


class ClientRefLogMessage(_RefLogMessage):
    """A client log message."""

    _logger_name: str = CERTDEPLOY_CLIENT_LOGGER_NAME


class ServerRefLogMessage(_RefLogMessage):
    """A server log message."""

    _logger_name: str = CERTDEPLOY_SERVER_LOGGER_NAME


class ClientRefLogMessages:
    """Reference client log messages."""

    HAS_STARTED: ClientRefLogMessage = ClientRefLogMessage(
        'INFO',
        'Listening for incoming connections at ',
        'certdeploy.client.daemon.DeployServer.serve_forever'
    )
    HAS_UPDATED: ClientRefLogMessage = ClientRefLogMessage(
        'INFO',
        'Updated services',
        'certdeploy.client.daemon._Update.run'
    )
    HELP_TEXT: PlainText = PlainText(
        'Plain text',
        'Usage: certdeploy-client [OPTIONS]',
        'Command line output'
    )
    HELP_TEXT_ALT: PlainText = PlainText(
        'Plain text',
        'Usage: -typer-main [OPTIONS]',
        'CliRunner output'
    )
    MISSING_CONFIG: ClientRefLogMessage = ClientRefLogMessage(
        'ERROR',
        'Config file "/etc/certdeploy/client.yml" not found: [Errno 2] No such '
        'file or directory: \'/etc/certdeploy/client.yml\'',
        'a repackaged FileNotFound exception in '
        'certdeploy.client._main._typer_main'
    )


class ParamikoRefLogMessages:
    """Reference paramiko log messages."""

    EMPTY: _RefLogMessage = _RefLogMessage('DEBUG', '', 'made up',
                                           PARAMIKO_LOGGER_NAME)
    TRANSPORT_EMPTY: _RefLogMessage = _RefLogMessage(
        'DEBUG',
        '',
        'made up',
        f'{PARAMIKO_LOGGER_NAME}.transport'
    )
    TRANSPORT_SFTP_EMPTY: _RefLogMessage = _RefLogMessage(
        'DEBUG',
        '',
        'made up',
        f'{PARAMIKO_LOGGER_NAME}.transport.sftp'
    )


class ServerRefLogMessages:
    """Reference server log messages."""

    ADD_TO_QUEUE_MESSAGE: ServerRefLogMessage = ServerRefLogMessage(
        'DEBUG',
        'Adding lineage to queue.',
        'certdeploy.server._main._run'
    )
    HAS_STARTED: ServerRefLogMessage = ServerRefLogMessage(
        'DEBUG',
        'Server.serve_forever: one_shot=',
        'certdeploy.server.server.daemon.Server.serve_forever'
    )
    DAEMON_HAS_STARTED: ServerRefLogMessage = ServerRefLogMessage(
        'DEBUG',
        'Server.serve_forever: one_shot=False',
        'certdeploy.server.server.daemon.Server.serve_forever'
    )
    PUSH_HAS_STARTED: ServerRefLogMessage = ServerRefLogMessage(
        'DEBUG',
        # The `True` is the expected value of `one_shot` given it's push mode
        'Server.serve_forever: one_shot=True',
        'certdeploy.server.server.daemon.Server.serve_forever'
    )
    HELP_TEXT: PlainText = PlainText(
        'Plain text',
        'Usage: certdeploy-server [OPTIONS]',
        'Command line output'
    )
    HELP_TEXT_ALT: PlainText = PlainText(
        'Plain text',
        'Usage: -typer-main [OPTIONS]',
        'CliRunner output'
    )
    MISSING_CONFIG: ServerRefLogMessage = ServerRefLogMessage(
        'ERROR',
        'FileNotFoundError: [Errno 2] No such file or directory: '
        '\'/etc/certdeploy/server.yml\'',
        'a repackaged FileNotFound exception in '
        'certdeploy.server._main._typer_main'
    )
    # or domains
    MISSING_LINEAGE: ServerRefLogMessage = ServerRefLogMessage(
        'ERROR',
        'Could not find lineage or domains.',
        'certdeploy.server._main._run'
    )
    PUSH_ONLY: ServerRefLogMessage = ServerRefLogMessage(
        'DEBUG',
        'Running manual push without a running daemon',
        'certdeploy.server._main._run'
    )
    RENEW_ONLY: ServerRefLogMessage = ServerRefLogMessage(
        'DEBUG',
        'Running renew',
        'certdeploy.server._main._run'
    )


def log_level_int(log_level: str) -> int:
    """Convert `log_level` into an `int` log level from `logging`."""
    return getattr(logging, log_level.upper())


def log_level_eq(log_level_1: str, log_level_2: str) -> bool:
    """Test whether the two log levels are the same `int` log level."""
    return log_level_int(log_level_1) == log_level_int(log_level_2)


def log_level_gt(log_level_1: str, log_level_2: str) -> bool:
    """Test whether the `log_level_1` is a higher level than `log_level_2`."""
    return log_level_int(log_level_1) > log_level_int(log_level_2)


def log_level_lt(log_level_1: str, log_level_2: str) -> bool:
    """Test whether the `log_level_1` is a lower level than `log_level_2`."""
    return log_level_int(log_level_1) < log_level_int(log_level_2)


@pytest.fixture()
def log_file(tmp_path: pathlib.Path) -> pathlib.Path:
    """Returns a temporary log file."""
    return tmp_path.joinpath('tmp.log')
