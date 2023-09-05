
import enum
import logging
import os
from importlib.metadata import (  # pragma: no cover
    PackageNotFoundError,
    version
)
from typing import Any, Union

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__  # pylint: disable=invalid-name
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError


logging.basicConfig()


DEFAULT_CONFIG_DIR = '/etc/certdeploy'
DEFAULT_USERNAME = 'certdeploy'
DEFAULT_PORT = 22

DEFAULT_CLIENT_SOURCE_DIR = '/var/cache/certdeploy'
DEFAULT_CLIENT_CONFIG = os.path.join(DEFAULT_CONFIG_DIR, 'client.yml')
DEFAULT_CLIENT_DEST_DIR = '/etc/letsencrypt/live'

DEFAULT_SERVER_CONFIG = os.path.join(DEFAULT_CONFIG_DIR, 'server.yml')
DEFAULT_SERVER_HOST_KEYS = os.path.join(DEFAULT_CONFIG_DIR, 'server_hostkeys')

DEFAULT_LOG_DATE_FORMAT = '%Y.%m.%d-%H:%M:%S'
DEFAULT_LOG_FORMAT = '%(levelname)s:%(name)s: %(message)s'
CERTDEPLOY_CLIENT_LOGGER_NAME = 'certdeploy-client'
CERTDEPLOY_SERVER_LOGGER_NAME = 'certdeploy-server'
# This value can be obtained from
#   https://github.com/paramiko/paramiko/blob/main/paramiko/util.py
PARAMIKO_LOGGER_NAME = 'paramiko'


class LogLevel(enum.Enum):
    """Logging levels as an enum of strings."""

    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'

    @classmethod
    def cast(cls, level: Union[int, str, 'LogLevel']) -> 'LogLevel':
        if isinstance(level, cls):
            return level
        if isinstance(level, str):
            return cls.from_str(level)
        if isinstance(level, int):
            return cls.from_int(level)
        raise TypeError(f'Invalid log level: {level}')

    @classmethod
    def from_int(cls, level: int) -> 'LogLevel':
        for log_level in cls:
            if getattr(logging, log_level.value) == level:
                return log_level
        return None

    @classmethod
    def from_str(cls, level: str) -> 'LogLevel':
        for log_level in cls:
            if log_level.value == level:
                return log_level
        return None

    @classmethod
    def to_int(cls, level: Union[int, str, 'LogLevel']) -> int:
        return getattr(logging, cls.cast(level).value)

    @classmethod
    def to_str(cls, level: Union[int, str, 'LogLevel']) -> str:
        return cls.cast(level).value

    @classmethod
    def validate(cls, level: Union[int, str, 'LogLevel']) -> bool:
        try:
            if cls.cast(level):
                return True
            return False
        except TypeError:
            return False


def format_error(err, message_format='{name}: {message}'):
    """Format errors consistently."""
    return message_format.format(name=type(err).__name__, message=err)


class Logger:
    """A logging helper with some modified behavior."""

    def __init__(self, name: str):
        """Prepare the `Logger`.

        Arguments:
            name: The name of the `logging.Logger`.
        """
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

    def setLevel(self, level: Union[int, str, LogLevel]):
        """Set the logging level for this `Logger`.

        This is a more flexible implementation of `logging.Logger.setLevel`.

        Arguments:
            level: The desired log level as either the `logging` log level, the
                string log level, or the `LogLevel`.
        """
        self._log.setLevel(LogLevel.to_str(level))

    def __getattr__(self, attr: str):
        """Pass requests for missing attributes on to the `logging.Logger`."""
        if hasattr(self._log, attr):
            return getattr(self._log, attr)
        raise AttributeError(attr)


def set_log_properties(logger_name: str, log_filename: os.PathLike,
                       log_level: Union[int, str, LogLevel] = LogLevel.ERROR,
                       msg_format: str = DEFAULT_LOG_FORMAT,
                       date_format: str = DEFAULT_LOG_DATE_FORMAT):
    """Set the CertDeploy logger properties.

    Arguments:
        log_filename:
        log_level: The desired log level. Defaults to `LogLevel.ERROR`.
        msg_format: The format for the each log entry. Defaults to
            `DEFAULT_LOG_FORMAT`.
        date_format: The date format for each log entry. This is only used if
            the `msg_format` has the date in it. Defaults to
            `DEFAULT_LOG_DATE_FORMAT`.
    """
    logger = logging.getLogger(name=logger_name)
    if log_level:
        logger.setLevel(LogLevel.to_str(log_level))
    if log_filename:
        for old_handler in logger.handlers:
            logger.removeHandler(old_handler)
        log_file = open(log_filename, 'a')
        handler = logging.StreamHandler(log_file)
        handler.setFormatter(logging.Formatter(msg_format, date_format))
        logger.addHandler(handler)
