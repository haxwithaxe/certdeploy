
import py
import pytest

from certdeploy.client.config import ClientConfig
from certdeploy.errors import ConfigError


def test_accepts_valid_name(tmp_client_config_file: callable):
    """Verify the valid values for the `systemd` update service type are
    accepted.
    """
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
        'a_unit_name.scope'
    ]
    for name in names:
        config_filename, _ = tmp_client_config_file(
            update_services=[
                dict(type='systemd', name=name)
            ]
        )
        config = ClientConfig.load(config_filename)
        assert config.services[0].name == name


def test_fails_invalid_name_values(tmp_client_config_file: callable):
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
        'bad_character_*.service'
    ]
    for bad_name in bad_names:
        config_filename, _ = tmp_client_config_file(
            update_services=[
                dict(type='systemd', name=bad_name)
            ]
        )
        with pytest.raises(ConfigError) as err:
            ClientConfig.load(config_filename)
        assert (f'Invalid value "{bad_name}" for systemd update '
                f'service config `name`.' in str(err))


def test_fails_null_name_values(tmp_client_config_file: callable):
    """Verify ConfigError is thrown for `name` values that are null."""
    config_filename, _ = tmp_client_config_file(
        update_services=[
            dict(type='systemd', name=None)
        ]
    )
    with pytest.raises(ConfigError) as err:
        ClientConfig.load(config_filename)
    assert ('Invalid value "None" for systemd update service config `name`.' in
            str(err))


def test_fails_missing_name_values(tmp_client_config_file: callable,
                                   tmpdir: py.path.local):
    """Verify ConfigError is thrown for `name` values that are missing."""
    config_filename, _ = tmp_client_config_file(
        update_services=[
            dict(type='systemd')
        ]
    )
    with pytest.raises(ConfigError) as err:
        ClientConfig.load(config_filename)
    assert ('Invalid value "None" for systemd update service config `name`.' in
            str(err))
