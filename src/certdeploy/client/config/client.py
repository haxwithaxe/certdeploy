
import os
import shutil
from dataclasses import dataclass, field

import yaml

from ... import (
    DEFAULT_CLIENT_SOURCE_DIR,
    DEFAULT_PORT,
    DEFAULT_USERNAME,
    LogLevel
)


@dataclass
class SFTPDConfig:
    """CertDeploy client SFTP server config."""

    listen_port: int = DEFAULT_PORT
    """The port to listen on."""
    listen_address: str = ''
    """The IP address to listen on."""
    username: str = DEFAULT_USERNAME
    """The username to accept logins from."""
    privkey_filename: os.PathLike = None
    """The path of the private key file."""
    server_pubkey: str = None
    """The text of the public key to accept logins from."""
    server_pubkey_filename: os.PathLike = None
    """The path of the public key to accept logins from."""
    log_level: str = 'ERROR'
    """The paramiko log level. This is separate from the CertDeploy log level.
    """
    log_filename: os.PathLike = '/dev/stderr'
    """The path of the paramiko log file."""
    socket_backlog: int = 10
    """The number of connections to queue while handling the current
    connection.
    """


@dataclass
class Config:
    """CertDeploy client config."""

    destination: os.PathLike
    """The directory to deploy new certs to."""
    source: os.PathLike = DEFAULT_CLIENT_SOURCE_DIR
    """The directory to look for new certs in."""
    sftpd: dict = field(default_factory=dict)
    """A `dict` with arguments for `certdeploy.client.config.SFTPDConfig`."""
    systemd_exec: os.PathLike = shutil.which('systemctl')
    """The path of the ``systemctl`` executable."""
    systemd_timeout: int = None  # Wait indefinitely
    """The timeout for executing ``systemctl``. Defaults to `None` (wait
    indefinitely).
    """
    docker_url: str = 'unix://var/run/docker.sock'  # Use the local socket
    """The URI of the docker socket."""
    update_services: list[dict] = field(default_factory=list)
    """A list of `certdeploy.client.update.Service` keyword argument `dict`."""
    update_delay: str = '1h'
    """The interval to delay before running the updates. Defaults to ``1h``.
    The format is `<multiplier><unit>` with one or more multiplier-unit pairs.
    For example a week and 2 days would be ``1w2d``. The following unit
    suffixes can be used:

            * `s`: second
            * `m`: minute
            * `h`: hour
            * `d`: day
            * `w`: week

    """
    fail_fast: bool = False
    """Exit on the first failed action if `True`."""
    log_level: LogLevel = LogLevel.ERROR.value
    """The log level of the CertDeploy client. Valid values are `DEBUG`,
    `INFO`, `WARNING`, `ERROR`, and `CRITICAL`.
    """

    @classmethod
    def load(cls, filename: os.PathLike):
        """Load the config from a file."""
        with open(filename, 'r', encoding='utf-8') as config_file:
            config = yaml.safe_load(config_file)
        return cls(**config)
