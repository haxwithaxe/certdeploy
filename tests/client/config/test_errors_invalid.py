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
