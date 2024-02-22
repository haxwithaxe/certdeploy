"""Tests to verify the behavior of the rc service update type."""

from typing import Callable

import pytest
from fixtures.errors import ClientErrors
from fixtures.utils import ConfigContext

from certdeploy.client.config import ClientConfig
from certdeploy.errors import ConfigError


def test_accepts_valid_name(
    tmp_client_config_file: Callable[[...], ConfigContext],
):
    pass


def test_accepts_valid_timeout_int(
    tmp_client_config_file: Callable[[...], ConfigContext],
):
    timeout = 11
    context = tmp_client_config_file(
        update_services=[
            dict(
                type='rc',
                name='test-rc-service-name',
                timeout=timeout,
            )
        ],
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].timeout == timeout


def test_accepts_valid_timeout_float(
    tmp_client_config_file: Callable[[...], ConfigContext],
):
    timeout = 11.7
    context = tmp_client_config_file(
        update_services=[
            dict(
                type='rc',
                name='test-rc-service-name',
                timeout=timeout,
            )
        ],
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].timeout == timeout


def test_gets_default_timeout(
    tmp_client_config_file: Callable[[...], ConfigContext],
):
    timeout = 13.37
    context = tmp_client_config_file(
        init_timeout=timeout,
        update_services=[dict(type='rc', name='test-rc-service-name')],
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].timeout == timeout


def test_overrides_timeout_with_none(
    tmp_client_config_file: Callable[[...], ConfigContext],
):
    context = tmp_client_config_file(
        init_timeout=23,
        update_services=[
            dict(
                type='rc',
                name='test-rc-service-name',
                timeout=False,
            )
        ],
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].timeout is None


def test_overrides_timeout_with_int(
    tmp_client_config_file: Callable[[...], ConfigContext],
):
    timeout = 37
    context = tmp_client_config_file(
        init_timeout=29,
        update_services=[
            dict(
                type='rc',
                name='test-rc-service-name',
                timeout=timeout,
            )
        ],
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].timeout == timeout


def test_fails_null_name_values(
    tmp_client_config_file: Callable[[...], ConfigContext],
):
    """Verify ConfigError is thrown for `name` values that are null."""
    context = tmp_client_config_file(
        update_services=[dict(type='rc', name=None)],
    )
    with pytest.raises(ConfigError) as err:
        ClientConfig.load(context.config_path)
    assert ClientErrors.format_invalid_value(
        'name', 'None', 'rc service update config'
    ) in str(err)


def test_fails_missing_name_values(
    tmp_client_config_file: Callable[[...], ConfigContext]
):
    """Verify ConfigError is thrown for `name` values that are missing."""
    context = tmp_client_config_file(update_services=[dict(type='rc')])
    with pytest.raises(ConfigError) as err:
        ClientConfig.load(context.config_path)
    assert ClientErrors.format_invalid_value(
        'name', 'None', 'rc service update config'
    ) in str(err)


def test_fails_invalid_action_value(
    tmp_client_config_file: Callable[[...], ConfigContext],
):
    """Verify ConfigError is thrown for invalid `action` values."""
    context = tmp_client_config_file(
        update_services=[
            dict(
                type='rc',
                name='valid-name',
                action='invalid action',
            )
        ],
    )
    with pytest.raises(ConfigError) as err:
        ClientConfig.load(context.config_path)
    assert ClientErrors.format_invalid_value(
        key='action', value='invalid action', config_desc='service valid-name'
    ) in str(err)
