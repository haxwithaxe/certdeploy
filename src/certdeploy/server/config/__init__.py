
import os
from typing import Optional

import yaml

from ... import LogLevel
from ...errors import ConfigError
from .client import ClientConnection
from .server import Server


class ServerConfig(Server):
    """Server configuration."""

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
                        raise ConfigError('Invalid client config option:'
                                          f' {err}') from err
                    raise
        else:
            raise ConfigError('No client configs given.')

    @classmethod
    def load(
        cls,
        filename: os.PathLike,
        override_log_file: Optional[os.PathLike] = None,
        override_log_level: Optional[LogLevel] = None,
        override_sftp_log_file: Optional[os.PathLike] = None,
        override_sftp_log_level: Optional[LogLevel] = None
    ):
        """Load the `ServerConfig` from a file."""
        with open(filename, 'r', encoding='utf-8') as config_file:
            config = yaml.safe_load(config_file)
        if override_sftp_log_level:
            config['sftp_log_level'] = override_sftp_log_level
        if override_sftp_log_file:
            config['sftp_log_filename'] = override_sftp_log_file
        if override_log_level:
            config['log_level'] = override_log_level
        if override_log_file:
            config['log_filename'] = override_log_file
        return cls(**config)
