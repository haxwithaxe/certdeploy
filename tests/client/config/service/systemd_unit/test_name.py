"""Tests to verify the behavior of the systemd service update type."""

from typing import Callable

import pytest
from fixtures.errors import ClientErrors
from fixtures.utils import ConfigContext

from certdeploy.client.config import ClientConfig
from certdeploy.errors import ConfigError


def test_accepts_valid_name(
    tmp_client_config_file: Callable[[...], ConfigContext],
    tmp_path_factory: pytest.TempPathFactory,
):
    """Verify the valid values for the `systemd` are accepted."""
    names = [
        'a-z0-9:_,.\\-@a-z0-9:_,.\\-.service',
        'a-z0-9:_,.\\-.service',
        'a_unit_name.service',
        'a_unit_name.socket',
        'a_unit_name.device',
        'a_unit_name.mount',
        'a_unit_name.automount',
        'a_unit_name.swap',
        'a_unit_name.target',
        'a_unit_name.path',
        'a_unit_name.timer',
        'a_unit_name.slice',
        'a_unit_name.scope',
    ]
    for name in names:
        context = tmp_client_config_file(
            tmp_path=tmp_path_factory.mktemp('test_accepts_valid_name'),
            update_services=[dict(type='systemd', name=name)],
        )
        config = ClientConfig.load(context.config_path)
        assert config.services[0].name == name


def test_fails_invalid_name_values(
    tmp_client_config_file: Callable[[...], ConfigContext],
    tmp_path_factory: pytest.TempPathFactory,
):
    """Verify ConfigError is thrown for `name` values that are invalid.

    This is an exhaustive set of invalid names but these are important when it
    comes to shell injection.
    """
    bad_names = [
        'with spaces.service',
        'bad_extension.svc',
        'bad_character_;.service',
        'bad_character_/.service',
        'bad_character_>.service',
        'bad_character_<.service',
        'bad_character_&.service',
        'bad_character_|.service',
        'bad_character_+.service',
        'bad_character_*.service',
    ]
    for bad_name in bad_names:
        context = tmp_client_config_file(
            tmp_path=tmp_path_factory.mktemp('test_fails_invalid_name_values'),
            update_services=[dict(type='systemd', name=bad_name)],
        )
        with pytest.raises(ConfigError) as err:
            ClientConfig.load(context.config_path)
        assert ClientErrors.format_invalid_value(
            'name', bad_name, 'systemd update service config'
        ) in str(err)


def test_fails_null_name_values(
    tmp_client_config_file: Callable[[...], ConfigContext],
):
    """Verify ConfigError is thrown for `name` values that are null."""
    context = tmp_client_config_file(
        update_services=[dict(type='systemd', name=None)],
    )
    with pytest.raises(ConfigError) as err:
        ClientConfig.load(context.config_path)
    assert ClientErrors.format_invalid_value(
        'name', 'None', 'systemd update service config'
    ) in str(err)


def test_fails_missing_name_values(
    tmp_client_config_file: Callable[[...], ConfigContext]
):
    """Verify ConfigError is thrown for `name` values that are missing."""
    context = tmp_client_config_file(update_services=[dict(type='systemd')])
    with pytest.raises(ConfigError) as err:
        ClientConfig.load(context.config_path)
    assert ClientErrors.format_invalid_value(
        'name', 'None', 'systemd update service config'
    ) in str(err)
