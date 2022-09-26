import os

import pytest

from certdeploy.errors import ConfigError
from certdeploy.server.config import ServerConfig


def test_fails_invalid_key(tmp_server_config: callable):
    config_filename, src_config = tmp_server_config(bad_config=True)
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(config_filename)
    assert 'Invalid config option: ' in str(err)


def test_fails_nonexistent_privkey(tmp_server_config: callable):
    assert not os.path.exists('/nonexistent/privkey')
    config_filename, src_config = tmp_server_config(
        privkey_filename='/nonexistent/privkey'
    )
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(config_filename)
    assert 'The config `privkey_filename` must be a file.' in str(err)


def test_fails_missing_client_configs(tmp_server_config: callable):
    assert not os.path.exists('/nonexistent/privkey')
    config_filename, src_config = tmp_server_config(
        client_configs=[]
    )
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(config_filename)
    assert 'No client configs given.' in str(err)


def test_fails_invalid_client_key(tmp_server_config: callable,
                                  pubkeygen: callable):
    config_filename, src_config = tmp_server_config(
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


def test_fails_invalid_client_pubkey(tmp_server_config: callable,
                                     pubkeygen: callable):
    config_filename, src_config = tmp_server_config(
        client_configs=[dict(
            address='1.2.3.4',
            domains=['test.example.com'],
            pubkey='not a key'
        )]
    )
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(config_filename)
    assert 'Invalid value for `pubkey`: ' in str(err)
