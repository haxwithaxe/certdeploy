"""Fixtures and utilities for testing error conditions."""

from typing import Any, Callable

import pytest

INVALID_CONFIG_FMT: str = 'Invalid value "{value}" for {config_desc}`{key}`.'
INVALID_CONFIG_MUST_FMT: str = (
    'Invalid value "{value}" for {config_desc}' '`{key}`. `{key}` must {must}.'
)
MISSING_SCRIPT_SERVICE_FILE_FMT = (
    'Script file "{path}" for service {name} ' 'not found.'
)
MISSING_DOCKER_SERVICE_FMT = (
    '''DockerServiceNotFound(\'DockerService failed to update: Could not '''
    '''find any docker service matching the following filter: '''
    '''{{\\\'label\\\': "{label}"}}\')'''
)


class Errors:
    """Base class for error strings and formatting."""

    INVALID_CONFIG_OPTION: str = 'Invalid config option: '
    MUST_DIR_EXISTS: str = 'be a directory that exists'
    SSH_BANNER_ERROR: str = 'Error reading SSH protocol banner'

    @staticmethod
    def format_invalid_value(
        key: str,
        value: Any,
        config_desc: str = '',
    ) -> str:
        """Format an invalid value message.

        Arguments:
            key: The config key.
            value: The value expected in the message as if it were given by the
                user.
            config_desc (optional): The optional config description.

        Returns:
            A formatted invalid value error string.
        """
        # Add a space to the description if it's set.
        if config_desc:
            config_desc = f'{config_desc} '
        return INVALID_CONFIG_FMT.format(
            key=key,
            value=value,
            config_desc=config_desc,
        )

    @staticmethod
    def format_invalid_value_must(
        key: str, value: Any, must: str, config_desc: str = ''
    ) -> str:
        """Format an invalid value message with a must clause.

        Arguments:
            key: The config key.
            value: The value expected in the message as if it were given by the
                user.
            must: The string describing the requirements for the config.
            config_desc (optional): The optional config description.

        Returns:
            A formatted invalid value error string with a must clause.
        """
        # Add a space to the description if it's set.
        if config_desc:
            config_desc = f'{config_desc} '
        return INVALID_CONFIG_MUST_FMT.format(
            key=key, value=value, must=must, config_desc=config_desc
        )

    @classmethod
    def format_invalid_number(
        cls,
        key: str,
        value: Any,
        is_type: str = 'number',
        optional: bool = False,
        gt: str = None,
        lt: str = None,
        ge: str = None,
        le: str = None,
        config_desc: str = '',
    ):
        if is_type == int:
            is_type = 'integer'
        elif is_type == float:
            is_type = 'float'
        if not isinstance(is_type, str):
            is_type = str(is_type)
        bounds = []
        bounds_str = ''
        if gt is not None:
            bounds.append(f'greater than {gt}')
        if lt is not None:
            bounds.append(f'less than {lt}')
        if ge is not None:
            bounds.append(f'greater than or equal to {ge}')
        if le is not None:
            bounds.append(f'less than or equal to {le}')
        if bounds:
            bounds_str = f' {" and ".join(bounds)}'
        if_set = ''
        if optional:
            if_set = ' if set'
        a_or_an = 'a'
        if is_type[0] in ('a', 'e', 'i', 'o', 'u'):
            a_or_an = 'an'
        return cls.format_invalid_value_must(
            key,
            value,
            must=f'be {a_or_an} {is_type}{bounds_str}{if_set}',
            config_desc=config_desc,
        )


class ClientErrors(Errors):
    """A collection of client errors and formatters."""

    INVALID_SFTPD_CONFIG_OPTION: str = 'Invalid SFTPD config option: '

    @staticmethod
    def format_missing_script_service(name: str, path: str):
        """Return a formatted missing script error message."""
        return MISSING_SCRIPT_SERVICE_FILE_FMT.format(name=name, path=path)

    @staticmethod
    def format_missing_docker_service(label: str):
        """Return a formatted missing docker service error message."""
        label = label.replace("'", """\\\'""")
        return MISSING_DOCKER_SERVICE_FMT.format(label=label)


class ServerErrors(Errors):
    """A collection of server errors and formatters."""

    NO_CLIENT_CONFIG: str = 'No client configs given.'
    INVALID_CLIENT_CONFIG_OPTION: str = 'Invalid client config option: '


@pytest.fixture(scope='function')
def format_invalid_value() -> Callable[[str, Any, str], str]:
    """Return an invalid config value error formatter."""
    return Errors.format_invalid_value


@pytest.fixture(scope='function')
def format_invalid_value_must() -> Callable[[str, Any, str], str]:
    """Return an invalid config value error with must clause formatter."""
    return Errors.format_invalid_value
