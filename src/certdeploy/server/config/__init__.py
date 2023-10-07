"""The CertDeploy server config."""

import os
from typing import Optional

import yaml

from ... import LogLevel
from ...errors import ConfigError
from .client import ClientConnection
from .server import Server


class ServerConfig(Server):
    """Server configuration.

    See `certdeploy.server.config.server.Server` for arguments and keyword
    arguments.
    """

    def __init__(self, *args, **kwargs):
        try:
            super().__init__(*args, **kwargs)
        except TypeError as err:
            if 'got an unexpected keyword argument' in str(err):
                raise ConfigError(f'Invalid config option: {err}') from err
            raise
        self.clients = []
        if self.client_configs:
            for client_config in self.client_configs:
                try:
                    self.clients.append(ClientConnection(**client_config))
                except TypeError as err:
                    if 'got an unexpected keyword argument' in str(err):
                        raise ConfigError(
                            'Invalid client config option:' f' {err}'
                        ) from err
                    raise
        else:
            raise ConfigError('No client configs given.')

    @classmethod
    def load(
        cls,
        filename: os.PathLike,
        override_log_filename: Optional[os.PathLike] = None,
        override_log_level: Optional[LogLevel] = None,
        override_sftp_log_filename: Optional[os.PathLike] = None,
        override_sftp_log_level: Optional[LogLevel] = None,
    ) -> 'ServerConfig':
        """Load the `ServerConfig` from a file.

        Arguments:
            filename: The path of the CertDeploy server config.
            override_log_filename: The path of the CertDeploy log file as given
                by the command line arguments. Defaults to the `log_filename`
                option in the config.
            override_log_level: The CertDeploy log level as given by the command
                line arguments. Defaults to the `log_level` option in the
                config.
            override_sftp_log_filename: The path of the SFTP client log file as
                given by the command line arguments. Defaults to the
                `sftp_log_level` option in the config.
            override_sftp_log_level: The SFTP client log level as given by the
                command line arguments. Defaults to the `log_level` option in
                the config.
        """
        with open(filename, 'r', encoding='utf-8') as config_file:
            config = yaml.safe_load(config_file)
        if override_sftp_log_level:
            config['sftp_log_level'] = override_sftp_log_level
        if override_sftp_log_filename:
            config['sftp_log_filename'] = override_sftp_log_filename
        if override_log_level:
            config['log_level'] = override_log_level
        if override_log_filename:
            config['log_filename'] = override_log_filename
        return cls(**config)
