
import os
import re
from typing import Any

from ...errors import ConfigError, ConfigInvalid, ConfigInvalidPath
from .client import Config, SFTPDConfig
from .service import Service

_DURATION_FACTORS = {
    'w': 60 * 60 * 24 * 7,
    'd': 60 * 60 * 24,
    'h': 60 * 60,
    'm': 60,
    's': 1
    }
# pylint: disable=consider-using-f-string
_DURATION_RE = re.compile(r'\s*(?:\s*(\d+(?:\.\d+)?)([{0}]))\s*'.format(
    ''.join(_DURATION_FACTORS.keys())
))
# pylint: enable=consider-using-f-string


class ClientConfig(Config):  # pylint: disable=too-few-public-methods
    """CertDeploy client configuration."""
    # This is meant to validate as much of the config as possible so that
    #   errors are more likely to occur while a human is looking and before
    #   the system is cluttered with possible causes.

    def __init__(self, *args: Any, **kwargs: Any):
        try:
            super().__init__(*args, **kwargs)
        except TypeError as err:
            if 'got an unexpected keyword argument' in str(err):
                raise ConfigError('Invalid config option: {err}') from err
            raise
        if not os.path.isdir(self.source):
            raise ConfigInvalidPath('source', self.source, is_type='directory')
        if not os.path.isdir(self.destination):
            raise ConfigInvalidPath('destination', self.destination,
                                    is_type='directory')
        self.services = [Service.load(s) for s in self.update_services]
        try:
            self.sftpd_config = SFTPDConfig(**self.sftpd)
        except TypeError as err:
            if 'got an unexpected keyword argument' in str(err):
                raise ConfigError('Invalid SFTPD config option: {err}') from err
            raise
        seconds = 0
        # `null` in the config is eqivalent to 0s
        if self.update_delay is not None:
            matches = _DURATION_RE.findall(self.update_delay)
            # something to match against but no matches is bad
            if not matches:
                raise ConfigInvalid('update_delay', self.update_delay)
            try:
                for match in matches:
                    seconds += (float(match[0]) *
                                _DURATION_FACTORS[match[1]])
            except TypeError as err:
                raise ConfigInvalid('update_delay', self.update_delay) from err
        self.update_delay_seconds = int(seconds)
