"""Public CertDeploy Client Config."""

import os
import re
from typing import Any

# fmt: off
from ... import (
    CERTDEPLOY_CLIENT_LOGGER_NAME,
    set_log_properties,
    set_paramiko_log_properties,
)

# fmt: on
from ...errors import ConfigError, ConfigInvalid, ConfigInvalidPath
from .client import Config, Permissions, SFTPDConfig
from .service import DockerContainer, RCService, Script, Service, SystemdUnit

_DURATION_FACTORS = {
    'w': 60 * 60 * 24 * 7,
    'd': 60 * 60 * 24,
    'h': 60 * 60,
    'm': 60,
    's': 1,
}
_DURATION_RE = re.compile(
    r'\s*(?:\s*(\d+(?:\.\d+)?)([{0}]))\s*'.format(
        ''.join(_DURATION_FACTORS.keys()),
    )
)


class ClientConfig(Config):
    """CertDeploy client configuration.

    See `certdeploy.client.config.client.Config` for details about
    arguments.
    """

    # This is meant to validate as much of the config as possible so that
    #   errors are more likely to occur while a human is looking and before
    #   the system is cluttered with possible causes.

    def __init__(self, *args: Any, **kwargs: Any):
        try:
            super().__init__(*args, **kwargs)
        except TypeError as err:
            if 'got an unexpected keyword argument' in str(err):
                raise ConfigError(f'Invalid config option: {err}') from err
            raise
        # Set the log files right away so that the errors produced here go to
        #   the right place
        set_log_properties(
            logger_name=CERTDEPLOY_CLIENT_LOGGER_NAME,
            log_filename=self.log_filename,
            log_level=self.log_level,
        )
        if not os.path.isdir(self.source):
            raise ConfigInvalidPath('source', self.source, is_type='directory')
        if not os.path.isdir(self.destination):
            raise ConfigInvalidPath(
                'destination',
                self.destination,
                is_type='directory',
            )
        if isinstance(self.docker_timeout, (float, int)):
            DockerContainer.timeout = self.docker_timeout
        if isinstance(self.init_timeout, (float, int)):
            RCService.timeout = self.init_timeout
            SystemdUnit.timeout = self.init_timeout
        if isinstance(self.script_timeout, (float, int)):
            Script.timeout = self.script_timeout
        self.services = [Service.load(s) for s in self.update_services]
        try:
            self.sftpd_config = SFTPDConfig(**self.sftpd)
        except TypeError as err:
            if 'got an unexpected keyword argument' in str(err):
                raise ConfigError(
                    f'Invalid SFTPD config option: {err}',
                ) from err
            raise
        set_paramiko_log_properties(
            log_filename=self.sftpd_config.log_filename,
            log_level=self.sftpd_config.log_level,
        )
        seconds = 0
        # `null` in the config is eqivalent to 0s
        if self.update_delay is not None:
            matches = _DURATION_RE.findall(self.update_delay)
            # something to match against but no matches is bad
            if not matches:
                raise ConfigInvalid('update_delay', self.update_delay)
            try:
                for match in matches:
                    seconds += float(match[0]) * _DURATION_FACTORS[match[1]]
            except TypeError as err:
                raise ConfigInvalid('update_delay', self.update_delay) from err
        self.update_delay_seconds = int(seconds)
        try:
            self.permissions = Permissions(**self.file_permissions)
        except TypeError as err:
            if 'got an unexpected keyword argument' in str(err):
                raise ConfigError(
                    f'Invalid Permissions config option: {err}',
                ) from err
            raise
