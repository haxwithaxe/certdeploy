"""Tests to verify the behavior of the rc service update type."""

from typing import Callable

import pytest
from fixtures.errors import ClientErrors
from fixtures.utils import ConfigContext

from certdeploy.client.config import ClientConfig
from certdeploy.errors import ConfigError


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
