"""Verify various invalid configs produce `ConfigError`."""

import pathlib

import pytest
from fixtures.errors import ClientErrors

from certdeploy.client.config import ClientConfig
from certdeploy.errors import ConfigError


def test_config_invalid_source(tmp_path: pathlib.Path):
    """Verify an invalid `source` config produces a `ConfigError`."""
    bad_source = '/dev/null'
    with pytest.raises(ConfigError) as err:
        ClientConfig(destination=tmp_path, source=bad_source)
    assert ClientErrors.format_invalid_value_must(
        'source', bad_source, ClientErrors.MUST_DIR_EXISTS
    ) in str(err)


def test_config_invalid_destination(tmp_path: pathlib.Path):
    """Verify an invalid `destination` config produces a `ConfigError`."""
    bad_dest = '/dev/null'
    with pytest.raises(ConfigError) as err:
        ClientConfig(destination=bad_dest, source=tmp_path)
    assert ClientErrors.format_invalid_value_must(
        'destination', bad_dest, ClientErrors.MUST_DIR_EXISTS
    ) in str(err)


def test_config_invalid_update_delay(tmp_path: pathlib.Path):
    """Verify an invalid `update_delay` config produces a `ConfigError`."""
    bad_update_delay = 'invalid'
    with pytest.raises(ConfigError) as err:
        ClientConfig(
            destination=tmp_path,
            source=tmp_path,
            update_delay='invalid',
        )
    error_value = ClientErrors.format_invalid_value(
        'update_delay',
        bad_update_delay,
    )
    assert error_value in str(err)


def test_config_invalid_config_key(tmp_path: pathlib.Path):
    """Verify an invalid `ClientConfig` config key produces a `ConfigError`."""
    with pytest.raises(ConfigError) as err:
        ClientConfig(invalid_key=True)
    assert ClientErrors.INVALID_CONFIG_OPTION in str(err)


def test_config_invalid_sftpd_config_key(tmp_path: pathlib.Path):
    """Verify an invalid `SFTPDConfig` config key produces a `ConfigError`."""
    with pytest.raises(ConfigError) as err:
        ClientConfig(
            destination=tmp_path,
            source=tmp_path,
            sftpd={'invalid_key': True},
        )
    assert ClientErrors.INVALID_SFTPD_CONFIG_OPTION in str(err)


def test_config_invalid_permissions_user(tmp_path: pathlib.Path):
    """Verify an invalid `permissions.owner` config produces a `ConfigError`."""
    bad_owner = 1.2
    with pytest.raises(ConfigError) as err:
        ClientConfig(
            destination=tmp_path,
            source=tmp_path,
            file_permissions={'owner': bad_owner},
        )
    error_value = ClientErrors.format_invalid_value_must(
        'permissions.owner',
        bad_owner,
        must='be a user name (string) or UID (integer)',
    )
    assert error_value in str(err)


def test_config_invalid_permissions_group(tmp_path: pathlib.Path):
    """Verify an invalid `permissions.group` config produces a `ConfigError`."""
    bad_group = 1.5
    with pytest.raises(ConfigError) as err:
        ClientConfig(
            destination=tmp_path,
            source=tmp_path,
            file_permissions={'group': bad_group},
        )
    error_value = ClientErrors.format_invalid_value_must(
        'permissions.group',
        bad_group,
        must='be a group name (string) or GID (integer)',
    )
    assert error_value in str(err)


def test_config_invalid_permissions_mode(tmp_path: pathlib.Path):
    """Verify an invalid `permissions.mode` config produces a `ConfigError`."""
    bad_mode = '0x1'
    with pytest.raises(ConfigError) as err:
        ClientConfig(
            destination=tmp_path,
            source=tmp_path,
            file_permissions={'mode': bad_mode},
        )
    error_value = ClientErrors.format_invalid_number(
        'permissions.mode',
        bad_mode,
        is_type='integer',
        optional=True,
        ge=0,
        le=0o777,
    )
    assert error_value in str(err)


def test_config_invalid_permissions_directory_mode(tmp_path: pathlib.Path):
    """Verify invalid `permissions.directory_mode` config produces an error."""
    bad_mode = '0x3'
    with pytest.raises(ConfigError) as err:
        ClientConfig(
            destination=tmp_path,
            source=tmp_path,
            file_permissions={'directory_mode': bad_mode},
        )
    error_value = ClientErrors.format_invalid_number(
        'permissions.directory_mode',
        bad_mode,
        is_type='integer',
        optional=True,
        ge=0,
        le=0o777,
    )
    assert error_value in str(err)
