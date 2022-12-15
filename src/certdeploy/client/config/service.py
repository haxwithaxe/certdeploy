
import os
import re
import shutil
from typing import Union

from ...errors import ConfigError, ConfigInvalid, ConfigInvalidNumber
from .. import log

_DOCKER_NAME_RE = re.compile(r'[a-z0-9_.-]+', flags=re.I)
_SYSTEMCTL_ACTIONS = ('restart', 'reload')
_SYSTEMD_UNIT_NAME_RE = re.compile(
    r'[a-z0-9:_,.\\-]+(@[a-z0-9:_,.\\-]+)?\.'
    r'(service|socket|device|mount|automount|swap|target|path|timer|slice|'
    r'scope)',
    flags=re.I
)


class Service:
    """Service config base class.

    Note: Some simple validation is done in this base class and its subclasses.
        The goal is to catch obvious mistakes like invalid names or values of
        the wrong type.

    """

    action: str = None
    filters: dict = {}
    name: str = None  # Just so it's there when exceptions look for it
    timeout: Union[float, int] = None

    def __init__(self, config: dict):
        log.debug(
            'New service %s from config: config=%s',
            self.__class__.__name__,
            config
        )
        # name comes first to let errors reference it
        self.name = self._validate_name(config.get('name'))
        self.action = self._validate_action(config.get('action'))
        self.filters = self._validate_filters(config.get('filters'))
        self.timeout = self._validate_timeout(config.get('timeout'))
        log.debug('New service: %s', self)

    def _validate_action(self, action: str) -> str:
        return action or self.action

    def _validate_filters(self, filters):
        if filters is not None and not isinstance(filters, dict):
            raise ConfigError(f'Invalid value {filters} for `filters` for '
                              f'service {self.name}. `filters` must be a '
                              'dictionary or `null`.')
        return filters or self.filters

    def _validate_timeout(self, timeout: Union[float, int]
                          ) -> Union[float, int]:
        if timeout is not None and not isinstance(timeout, (float, int)):
            raise ConfigInvalidNumber('timeout', timeout, optional=True,
                                      config_desc=f'service {self.name}')
        # If timeout is an int or float (it's int float or None given the above)
        #   use it otherwise use the default (self.timeout). This is needed for
        #   DockerContainer. Otherwise this could just return timeout.
        return timeout if timeout is not None else self.timeout

    def _validate_name(self, name: str) -> str:
        # Don't return self.name since it always needs to be set or None.
        return name

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return (self.action == other.action and self.filters == other.filters
                and self.name == other.name and self.timeout == other.timeout)

    def __repr__(self) -> str:
        return (f'<{self.__class__.__name__}: action={self.action}, '
                f'filters={self.filters}, name={self.name}, '
                f'timeout={self.timeout}>')

    @staticmethod
    def load(config: dict) -> 'Service':
        """Load an update service model from a config dict.

        Arguments:
            config (dict): An update service config `dict`. The only required
                key for all types of services is `type`. Which is used to
                specify the type of service. Each service type has its own
                required config keys beyond `type`.

        """
        try:
            service_class = {
                'docker_container': DockerContainer,
                'docker_service': DockerService,
                'script': Script,
                'systemd': SystemdUnit
            }[config.get('type')]
        except KeyError as err:
            raise ConfigError(f'{config.get("type")} is not a valid service '
                              'type.') from err
        return service_class(config)


class DockerService(Service):  # pylint: disable=too-few-public-methods
    """Docker service update config.

    Notes:
        * If no value is given for `filters` in `config` and `name` is given
            filters will be set to exactly match `name`.
        * If no value is given for both `filters` and `name` in `config`,
            `ConfigError` is raised.

    """

    _type = 'service'

    def __init__(self, config: dict):
        super().__init__(config)
        if not self.name and not self.filters:
            raise ConfigError('Either `filters` or `name` must be given in '
                              '`docker_{self._type}` configs. Got: {config}.')
        if self.name and not self.filters:
            # Match the exact name as given
            self.filters = {'name': f'^{self.name}$'}

    def _validate_name(self, name: str) -> str:
        if name is None:
            return name
        if not name or not _DOCKER_NAME_RE.match(name.strip()):
            raise ConfigInvalid('name', name,
                                config_desc=f'docker {self._type} config')
        return name.strip()


class DockerContainer(DockerService):  # pylint: disable=too-few-public-methods
    """Docker container update config."""

    _type = 'container'
    action = 'restart'
    """The default update method."""
    timeout = 10
    """The default time to wait before giving up on preforming `action`."""


class Script(Service):  # pylint: disable=too-few-public-methods
    """Script based update config.

    Note:
        The value of name is made into an absolute path as part of
            validation. This means any relative paths are evaluated relative to
            the current working directory of the client if they aren't found
            with `shutil.which()`. If the script isn't found `ConfigError` is
            raised.

    """

    def __init__(self, config: dict):
        super().__init__(config)
        if os.path.isabs(self.name):
            self.script_path = self.name
        elif shutil.which(self.name):
            self.script_path = shutil.which(self.name)
        else:
            self.script_path = os.path.abspath(self.name)
        if not os.path.exists(self.script_path):
            raise ConfigError(f'Script file "{self.script_path}" for service '
                              f'{self.name} not found.')

    def _validate_name(self, name: str) -> str:
        if not name:
            raise ConfigInvalid('name', name, config_desc='script config')
        return name


class SystemdUnit(Service):  # pylint: disable=too-few-public-methods
    """Systemd unit update config.

    Note: `action` and `name` are validated. `action` has to be either
        ``reload`` or ``restart``. `name` must be a valid Systemd unit name. It
        doesn't have to exist on the system to pass validation it just has to
        look right.

    """

    action: str = 'restart'
    """The default update method for updating `systemd` services. Valid values
    are ``reload`` or ``restart``.
    """

    def _validate_action(self, action: str) -> str:
        if not action:
            return self.action
        if action.lower().strip() in _SYSTEMCTL_ACTIONS:
            return action.lower().strip()
        raise ConfigInvalid('action', action,
                            config_desc=f'service {self.name}')

    def _validate_name(self, name: str) -> str:
        if not name or not _SYSTEMD_UNIT_NAME_RE.match(name.strip()):
            raise ConfigInvalid('name', name,
                                config_desc='systemd update service config')
        return name.strip()
