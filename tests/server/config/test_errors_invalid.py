import os

import pytest

from certdeploy.errors import ConfigError
from certdeploy.server.config import ServerConfig


def test_fails_invalid_key(tmp_server_config_file: callable):
    config_filename, src_config = tmp_server_config_file(bad_config=True)
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(config_filename)
    assert 'Invalid config option: ' in str(err)


def test_fails_nonexistent_privkey(tmp_server_config_file: callable):
    assert not os.path.exists('/nonexistent/privkey')
    config_filename, src_config = tmp_server_config_file(
        privkey_filename='/nonexistent/privkey'
    )
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(config_filename)
    assert ('Invalid value "/nonexistent/privkey" for '
            '`privkey_filename`.') in str(err)


def test_fails_missing_client_configs(tmp_server_config_file: callable):
    assert not os.path.exists('/nonexistent/privkey')
    config_filename, src_config = tmp_server_config_file(
        client_configs=[]
    )
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(config_filename)
    assert 'No client configs given.' in str(err)


def test_fails_invalid_client_key(tmp_server_config_file: callable,
                                  pubkeygen: callable):
    config_filename, src_config = tmp_server_config_file(
        client_configs=[dict(
            address='1.2.3.4',
            domains=['test.example.com'],
            pubkey=pubkeygen(),
            bad_config=True
        )]
    )
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(config_filename)
    assert 'Invalid client config option: ' in str(err)


def test_fails_invalid_client_pubkey(tmp_server_config_file: callable,
                                     pubkeygen: callable):
    config_filename, src_config = tmp_server_config_file(
        client_configs=[dict(
            address='1.2.3.4',
            domains=['test.example.com'],
            pubkey='not a key'
        )]
    )
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(config_filename)
    assert 'Invalid value for `pubkey`: ' in str(err)


def test_fails_invalid_push_mode(tmp_server_config_file: callable):
    config_filename, src_config = tmp_server_config_file(
        push_mode='Invalid push_mode'
    )
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(config_filename)
    assert 'Invalid value "Invalid push_mode" for `push_mode`' in str(err)


def test_fails_invalid_push_interval(tmp_server_config_file: callable):
    config_filename, src_config = tmp_server_config_file(
        push_interval=-1
    )
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(config_filename)
    assert 'Invalid value "-1" for `push_interval`' in str(err)


def test_fails_invalid_push_retries(tmp_server_config_file: callable):
    config_filename, src_config = tmp_server_config_file(
        push_retries=-1
    )
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(config_filename)
    assert 'Invalid value "-1" for `push_retries`' in str(err)


def test_fails_invalid_push_retry_interval(tmp_server_config_file: callable):
    config_filename, src_config = tmp_server_config_file(
        push_retry_interval=-1
    )
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(config_filename)
    assert 'Invalid value "-1" for `push_retry_interval`' in str(err)


def test_fails_invalid_join_timeout(tmp_server_config_file: callable):
    config_filename, src_config = tmp_server_config_file(
        join_timeout=-1
    )
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(config_filename)
    assert 'Invalid value "-1" for `join_timeout`' in str(err)
