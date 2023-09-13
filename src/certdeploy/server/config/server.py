"""CertDeploy Server config backend."""

import enum
import os
import shutil
from dataclasses import dataclass, field
from typing import Any, Optional, Union

from ... import (
    CERTDEPLOY_SERVER_LOGGER_NAME,
    DEFAULT_SERVER_QUEUE_DIR,
    PARAMIKO_LOGGER_NAME,
    LogLevel,
    set_log_properties
)
from ...errors import (
    ConfigError,
    ConfigInvalid,
    ConfigInvalidChoice,
    ConfigInvalidNumber,
    ConfigInvalidPath
)
from ._validation import is_int, is_optional_float

_UNITS = ('minute', 'hour', 'day', 'week')
_WEEKDAYS = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday',
             'sunday')


def _normalize_unit(unit: str, interval: int) -> str:
    """Convert `unit` to a plural if interval is not 1.

    Arguments:
        unit: The time unit string.
        interval: The time interval (number of units).

    Returns:
        A normalized unit string. Pluralized if `interval` is not 1.

    Raises:
        ConfigError: If `unit` is not a valid unit.
    """
    # `schedule` uses plurals for `minute`, `hour`, `day`, and `week` units but
    #   only when the interval is not 1, which is overly complicated. So the
    #   conversion is being done here to keep the docs and config simpler.
    norm_unit = unit.lower().strip()
    if norm_unit not in _WEEKDAYS + _UNITS:
        raise ConfigError('`renew_unit` needs to be a day of the week '
                          'or an interval unit (minute, hour, day, week) not: '
                          f'{unit}')
    if interval != 1:
        return f'{norm_unit}s'
    return norm_unit


class PushMode(enum.Enum):
    """Server push modes."""

    SERIAL = 'serial'
    PARALLEL = 'parallel'

    @classmethod
    def __call__(cls, value: Any) -> 'PushMode':
        """Return the push mode that corresponds to `value`.

        Raises:
            ValueError if `value` does not correspond to any push mode.
        """
        if isinstance(value, str):
            super().__call__(value.lower())
        super().__call__(value)

    @classmethod
    def choices(cls) -> list['PushMode']:
        """Return a list of available values."""
        return [cls.SERIAL, cls.PARALLEL]


@dataclass
class Server:
    """Base server configuration."""

    privkey_filename: os.PathLike
    """The path of the server's private key file."""
    client_configs: list[dict] = field(default_factory=list)
    """A list of `dict` defining `certbot.server.client.Client` keyword
    arguments.
    """
    fail_fast: bool = False
    """Exit on the first failed action. Defaults to `False`."""
    log_level: Union[LogLevel, str] = LogLevel.ERROR
    """The log level of the CertDeploy server. Valid values are `DEBUG`,
    `INFO`, `WARNING`, `ERROR`, and `CRITICAL`.
    """
    log_filename: Optional[os.PathLike] = None
    """The path of the CertDeploy server log file."""
    sftp_log_level: Union[LogLevel, str] = LogLevel.ERROR
    """The paramiko log level. This is separate from the CertDeploy log level.
    The valid values are the same as `log_level`.
    """
    sftp_log_filename: Optional[os.PathLike] = None
    """The path of the paramiko log file."""
    renew_every: int = 1
    """The interval to try to renew certs on. Valid values are integers greater
    than 0.
    """
    renew_unit: str = 'day'
    """The type of interval to try to renew certs on. Valid values are
    `minute`, `hour`, `day`, `week` and weekday names.
    """
    renew_at: Optional[str] = None
    """The time of day to try to renew certs. Formatted ``HH:MM`` for
    `renew_unit` more than ``hour`` and ``:MM`` for minutes within an hour.
    """
    renew_exec: str = shutil.which('certbot')
    """The path of the Certbot executable."""
    renew_args: list[str] = field(default_factory=lambda: ['renew'])
    """Arguments for the Certbot executable."""
    renew_timeout: Optional[int] = None
    """Timeout for the ``certbot renew`` command. `None` means wait
    indefinitely.
    """
    push_mode: PushMode = PushMode.SERIAL
    """The type of deployment to use. Defaults to `PushMode.SERIAL`.

    * `PushMode.Serial` causes the certs to be pushed to clients one client at
        a time.
    * `PushMode.PARALLEL` causes the certs to be pushed to all clients all at
        once.
    """
    push_interval: int = 0
    """The interval between the beginning of parallel pushes. Defaults to `0`.

    * `0` disables any delay between the beginning or parallel pushes to
        clients.
    * Any other positive integer is used as the number of seconds between
        beginning attempts to push certs to this client.
    """
    push_retries: int = 1
    """The number of times to retry pushing certs to clients. Defaults to `1`.

    This is overridden by the `push_retries` in client configs, on a per client
    basis.

    * `0` will cause the server to only try to push once (no retries).
    * Any other positive integer will cause the server to try to push certs
        to clients and retry for each client as many as that many times before
        giving up.
    """
    push_retry_interval: int = 30
    """The delay in seconds between retrying to push certs to clients. Defaults
    to `30`.

    This is overridden by the `push_retry_interval` in client configs, on a per
    client basis.

    * `0` disables any delay between retries.
    * Any other positive integer is used as the number of seconds between
        attempts to push certs to this client.
    """
    join_timeout: Optional[float] = None
    """The number of seconds to wait while joining `PushWorker` threads.
    Defaults to 60 seconds.

    * Any positive number (`float` or `int`) will be used as the number of
        seconds.
    * `None` will cause the join to wait indefinitely.
    """
    queue_dir: os.PathLike = DEFAULT_SERVER_QUEUE_DIR
    """The directory where runtime files will be stored.

    The queue and its lockfile are stored here.
    """

    def __post_init__(self):
        """Validate config values.

        Raises:
            ConfigInvalid: If any config values checked are invalid.
        """
        # Set the log files right away so that the errors produced here go to
        #   the right place
        set_log_properties(
            logger_name=CERTDEPLOY_SERVER_LOGGER_NAME,
            log_filename=self.log_filename,
            log_level=self.log_level
        )
        set_log_properties(
            logger_name=PARAMIKO_LOGGER_NAME,
            log_filename=self.sftp_log_filename,
            log_level=self.sftp_log_level
        )
        # Check that the private key exists
        if not os.path.isfile(self.privkey_filename):
            raise ConfigInvalidPath('privkey_filename', self.privkey_filename,
                                    is_type='file')
        # Check that the queue directory is an existing directory
        if not os.path.isdir(self.queue_dir):
            raise ConfigInvalidPath('queue_dir', self.queue_dir,
                                    is_type='directory')
        # Check if the queue directory is writable.
        try:
            open(os.path.join(self.queue_dir, 'test'), 'w').close()
        except OSError as err:
            raise ConfigInvalidPath('queue_dir', self.queue_dir, writable=True,
                                    is_type='directory') from err
        else:
            os.remove(os.path.join(self.queue_dir, 'test'))
        # Check if the push mode is a push mode
        try:
            self.push_mode = PushMode(self.push_mode)
        except ValueError as err:
            raise ConfigInvalidChoice(
                'push_mode',
                self.push_mode,
                choices=PushMode.choices()
            ) from err
        # Check that the push_interval is an integer >= 0
        if not is_int(self.push_interval, 0):
            raise ConfigInvalidNumber('push_interval', self.push_interval,
                                      is_type=int, ge=0)
        # Check that the push_retries is an integer >= 0
        if not is_int(self.push_retries, 0):
            raise ConfigInvalidNumber('push_retries', self.push_retries,
                                      is_type=int, ge=0)
        # Check that the push_retry_interval is an integer >= 0
        if not is_int(self.push_retry_interval, 0):
            raise ConfigInvalidNumber('push_retry_interval',
                                      self.push_retry_interval, is_type=int,
                                      ge=0)
        # Check that the join_timeout is a float or int >= 0 if it is set.
        if not is_optional_float(self.join_timeout, 0):
            raise ConfigInvalidNumber('join_timeout', self.join_timeout,
                                      is_type='float or integer', ge=0)
        # Check that the renew_every is an integer > 0
        if not is_int(self.renew_every, 1):
            raise ConfigInvalidNumber('renew_every', self.renew_every,
                                      is_type=int, optional=True, gt=0)
        # Normalize the renew_unit and check that it's valid
        self.renew_unit = _normalize_unit(self.renew_unit, self.renew_every)
        if self.renew_unit in _WEEKDAYS and self.renew_every != 1:
            raise ConfigInvalid('renew_unit', self.renew_unit, must=' not be a'
                                ' weekday if `renew_every` is set and not 1.')
