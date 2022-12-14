
import os

import yaml

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
    def load(cls, filename: os.PathLike):
        """Load the `ServerConfig` from a file."""
        with open(filename, 'r', encoding='utf-8') as config_file:
            config = yaml.safe_load(config_file)
        return cls(**config)
