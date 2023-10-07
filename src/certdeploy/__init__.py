"""Shared CertDeploy code."""

import enum
import logging
import os
import sys

# fmt: off
from importlib.metadata import (  # pragma: no cover
    PackageNotFoundError,
    version
)

# fmt: on
from typing import Any, Union

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__  # pylint: disable=invalid-name
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError

## Global default values
DEFAULT_CONFIG_DIR = '/etc/certdeploy'
# Default SFTP username for servers and clients
DEFAULT_USERNAME = 'certdeploy'
# Default SFTP port for servers and clients
DEFAULT_PORT = 22

# Default paths for clients
DEFAULT_CLIENT_SOURCE_DIR = '/var/cache/certdeploy'
DEFAULT_CLIENT_CONFIG = os.path.join(DEFAULT_CONFIG_DIR, 'client.yml')
DEFAULT_CLIENT_DEST_DIR = '/etc/letsencrypt/live'

# Default paths for servers
DEFAULT_SERVER_CONFIG = os.path.join(DEFAULT_CONFIG_DIR, 'server.yml')
DEFAULT_SERVER_HOST_KEYS = os.path.join(DEFAULT_CONFIG_DIR, 'server_hostkeys')
DEFAULT_SERVER_QUEUE_DIR = '/var/run/certdeploy'

# Default logging
DEFAULT_LOG_DATE_FORMAT = '%Y.%m.%d-%H:%M:%S'
DEFAULT_LOG_FORMAT = '%(levelname)s:%(name)s: %(message)s'
DEFAULT_LOG_FILENAME = '/dev/stdout'  # maps to sys.stdout
DEFAULT_LOG_LEVEL = logging.ERROR

## Logging Constants
CERTDEPLOY_CLIENT_LOGGER_NAME = 'certdeploy-client'
CERTDEPLOY_SERVER_LOGGER_NAME = 'certdeploy-server'
# This value can be obtained from
#   https://github.com/paramiko/paramiko/blob/main/paramiko/util.py
PARAMIKO_LOGGER_NAME = 'paramiko'


# Initialize logging ASAP
logging.basicConfig(
    format=DEFAULT_LOG_FORMAT,
    datefmt=DEFAULT_LOG_DATE_FORMAT,
    stream=sys.stdout,  # DEFAULT_LOG_FILENAME
    level=DEFAULT_LOG_LEVEL,
)


class LogLevel(enum.Enum):
    """Logging levels and utilities."""

    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'

    @classmethod
    def cast(cls, level: Union[int, str, 'LogLevel']) -> 'LogLevel':
        """Cast `level` to a `LogLevel`.

        Returns:
            A `LogLevel` corresponding to `level`.

        Raises:
            TypeError: When `level` does not correspond to any `LogLevel`.
        """
        if isinstance(level, cls):
            return level
        if isinstance(level, int):
            for log_level in cls:
                if getattr(logging, log_level.value) == level:
                    return log_level
        if isinstance(level, str):
            try:
                return getattr(cls, level)
            except AttributeError:
                pass
        raise ValueError(f'Invalid log level: {level}')

    @classmethod
    def validate(cls, level: Union[int, str, 'LogLevel']) -> bool:
        """Verify `level` is a valid `LogLevel` or equivalent.

        Arguments:
            level: A log level.

        Returns:
            `True` if `level` is a log level.
        """
        try:
            if cls.cast(level):
                return True
            return False
        except TypeError:
            return False

    def __int__(self) -> int:
        """Return an integer equivalent to a `logging` level."""
        return getattr(logging, self.value)

    def __str__(self) -> str:
        """Return a string representation of the log level."""
        return self.value


def format_error(
    err: Exception,
    message_format: str = '{name}: {message}',
) -> str:
    """Format errors consistently.

    Arguments:
        err: The exception to format.
        message_format: The format string (`.format` style) to apply the error
            to. The keys `name` and `message` are passed to the format string.
            Defaults to `'{name}: {message}'`.

    Returns:
        A formatted string with the name and message of the given error.
    """
    return message_format.format(name=type(err).__name__, message=err)


class Logger:
    """A logging helper with some modified behavior.

    Arguments:
        name: The name of the `logging.Logger`.
    """

    def __init__(self, name: str):  # noqa: D107
        self._log = logging.getLogger(name=name)

    def error(self, *args: Any, exc_info=None, **kwargs):
        """Log an error message.

        See `logging.error` for details. This method differs from
        `logging.error` in the following ways:

            * If the first argument is an exception it's formatted so the type
                is given and not just the message.
            * exc_info is ignored if the log level is anything but DEBUG.

        """
        if self._log.getEffectiveLevel() > logging.ERROR:
            return
        # Make the exception pretty
        if args and isinstance(args[0], Exception):
            message = format_error(args[0])
            args = [message] + list(args[1:])
        # Show traceback if log level is debug
        if self._log.getEffectiveLevel() == logging.DEBUG:
            self._log.error(*args, exc_info=exc_info, **kwargs)
        else:
            self._log.error(*args, **kwargs)

    def purgeHandlers(self):
        """Purge all handlers from the logger."""
        for old_handler in self._log.handlers:
            self._log.removeHandler(old_handler)

    def setLevel(self, level: Union[int, str, LogLevel]):
        """Set the logging level for this `Logger`.

        This is a more flexible implementation of `logging.Logger.setLevel`.

        Arguments:
            level: The desired log level as either the `logging` log level, the
                string log level, or the `LogLevel`.
        """
        self._log.setLevel(LogLevel.cast(level).value)

    @classmethod
    def fromLogger(cls, logger: logging.Logger) -> 'Logger':
        """Create a `Logger` from a `logging.Logger`.

        Arguments:
            logger: The source `logging.Logger`.

        Returns:
            A new `Logger` with `logger` as the wrapped logger.
        """
        _logger = cls('dummy')
        _logger._log = logger
        return _logger

    def __getattr__(self, attr: str):
        """Pass requests for missing attributes on to the `logging.Logger`."""
        if hasattr(self._log, attr):
            return getattr(self._log, attr)
        # Raising from here so the traceback stops here.
        raise AttributeError(attr)


def set_paramiko_log_properties(
    log_filename: os.PathLike = None,
    log_level: Union[int, str, LogLevel] = None,
    msg_format: str = DEFAULT_LOG_FORMAT,
    date_format: str = DEFAULT_LOG_DATE_FORMAT,
):
    """Set the paramiko logger properties.

    Arguments:
        log_filename: The path to the log file.
        log_level: The desired log level. Defaults to `LogLevel.ERROR`.
        msg_format: The format for the each log entry. Defaults to
            `DEFAULT_LOG_FORMAT`.
        date_format: The date format for each log entry. This is only used if
            the `msg_format` has the date in it. Defaults to
            `DEFAULT_LOG_DATE_FORMAT`.
    """
    if log_filename and not os.path.isfile(log_filename):
        with open(log_filename, 'w') as log_file:
            log_file.write('')
    set_log_properties(
        PARAMIKO_LOGGER_NAME,
        log_filename,
        log_level,
        msg_format,
        date_format,
    )


def set_log_properties(
    logger_name: str,
    log_filename: os.PathLike,
    log_level: Union[int, str, LogLevel] = None,
    msg_format: str = DEFAULT_LOG_FORMAT,
    date_format: str = DEFAULT_LOG_DATE_FORMAT,
):
    """Set logger properties.

    Arguments:
        logger_name: The name of the logger.
        log_filename: The path to the log file.
        log_level: The desired log level. Defaults to `LogLevel.ERROR`.
        msg_format: The format for the each log entry. Defaults to
            `DEFAULT_LOG_FORMAT`.
        date_format: The date format for each log entry. This is only used if
            the `msg_format` has the date in it. Defaults to
            `DEFAULT_LOG_DATE_FORMAT`.
    """
    logger = Logger(name=logger_name)
    if log_filename:
        logger.purgeHandlers()
        if log_filename == '/dev/null':
            handler = logging.NullHandler()
        else:
            if log_filename in ('/dev/stdout', 'stdout', sys.stdout.name):
                log_file = sys.stdout
            elif log_filename in ('/dev/stderr', 'stderr', sys.stderr.name):
                log_file = sys.stderr
            else:
                log_file = open(log_filename, 'a')
            handler = logging.StreamHandler(log_file)
        handler.setFormatter(logging.Formatter(msg_format, date_format))
        logger.addHandler(handler)
    if log_level:
        logger.setLevel(LogLevel.cast(log_level).value)
