
import pathlib

import pytest

from certdeploy.client.config import ClientConfig
from certdeploy.errors import ConfigError


def test_config_invalid_source(tmp_path: pathlib.Path):
    with pytest.raises(ConfigError) as err:
        ClientConfig(
            destination=tmp_path,
            source='/dev/null'
        )
    assert ('Invalid value "/dev/null" for `source`. `source` must be a '
            'directory that exists.') in str(err)


def test_config_invalid_destination(tmp_path: pathlib.Path):
    with pytest.raises(ConfigError) as err:
        ClientConfig(
            destination='/dev/null',
            source=tmp_path
        )
    assert ('Invalid value "/dev/null" for `destination`. `destination` must be'
            ' a directory that exists.') in str(err)


def test_config_invalid_sftpd_config_key(tmp_path: pathlib.Path):
    with pytest.raises(ConfigError) as err:
        ClientConfig(
            destination=tmp_path,
            source=tmp_path,
            sftpd={'invalid_key': True}
        )
    assert 'Invalid SFTPD config option: ' in str(err)


def test_config_invalid_update_delay(tmp_path: pathlib.Path):
    with pytest.raises(ConfigError) as err:
        ClientConfig(
            destination=tmp_path,
            source=tmp_path,
            update_delay='invalid'
        )
    assert 'Invalid value "invalid" for `update_delay`.' in str(err)


def test_config_invalid_config_key(tmp_path: pathlib.Path):
    with pytest.raises(ConfigError) as err:
        ClientConfig(
            invalid_key=True
        )
    assert 'Invalid config option: ' in str(err)
