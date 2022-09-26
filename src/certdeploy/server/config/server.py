
import os
import shutil
from dataclasses import dataclass, field
from typing import Optional, Union

from ... import LogLevel


@dataclass
class Server:
    """Server configuration."""

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
    renew_every: int = 1
    """The interval to try to renew certs on. Valid values are positive
    integers greater than 0.
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
