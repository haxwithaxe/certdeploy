
import enum
import logging
import os
from importlib.metadata import (  # pragma: no cover
    PackageNotFoundError,
    version
)
from typing import Union

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


class LogLevel(enum.Enum):

    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'


def format_error(err, message_format='{name}: {message}'):
    return message_format.format(name=type(err).__name__, message=err)


class Logger:

    def __init__(self, name):
        self._log = logging.getLogger(name=name)

    def error(self, *args, exc_info=None, **kwargs):
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

    def setLevel(self, level: Union[int, LogLevel]):
        if isinstance(level, LogLevel):
            level = getattr(logging, level.value)
        elif isinstance(level, str):
            level = getattr(logging, level.upper())
        self._log.setLevel(level)

    def __getattr__(self, attr):
        if hasattr(self._log, attr):
            return getattr(self._log, attr)
        raise AttributeError(attr)
