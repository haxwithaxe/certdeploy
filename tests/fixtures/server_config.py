
import pathlib

import pytest
import yaml

from certdeploy.server.config import ServerConfig


def _client_conn_config(pubkey: str, conf: dict = None) -> dict:
    _conf = dict(
        address='test_client_address',
        domains=['example.com'],
        pubkey=pubkey
    )
    if conf:
        _conf.update(conf)
    return _conf


@pytest.fixture(scope='function')
def client_conn_config_factory(pubkeygen: callable) -> callable:
    """Generate dicts to go into `client_configs`."""

    def _client_conn_config_factory(**conf) -> dict:
        return _client_conn_config(pubkeygen(), conf)

    return _client_conn_config_factory


def _server_config(tmp_path: pathlib.Path, pubkey: str, privkey: str,
                   conf: dict = None):
    queue_dir = tmp_path.joinpath('queue')
    queue_dir.mkdir()
    server_key = tmp_path.joinpath('server_key')
    server_key.write_text(privkey)
    config_path = tmp_path.joinpath('server.yml')
    # Non-default values for top level options
    config = dict(
        privkey_filename=str(server_key),
        client_configs=[_client_conn_config(pubkey)],
        # Has to be a real dir writable by the test user
        queue_dir=str(queue_dir)
    )
    if conf:
        config.update(conf)
    yaml.safe_dump(config, config_path.open('w'))
    return config_path, config


@pytest.fixture(scope='function')
def tmp_server_config_file(tmp_path_factory: pytest.TempPathFactory,
                           keypairgen: callable) -> callable:
    """Generate a full server config and config file.

    This sets all the possible values to non-default values to help test the
    ServerConfig.
    """

    def _get_config(**conf):
        tmp_path = tmp_path_factory.mktemp('server_config')
        privkey, _ = keypairgen()
        _, pubkey = keypairgen()
        _conf = dict(
            fail_fast=False,
            log_level='DEBUG',
            renew_every=2,
            renew_unit='hour',
            renew_at=':00',
            renew_exec='test_certbot',
            renew_args=['test_renew'],
            renew_timeout=None,
            push_mode='parallel',
            push_interval=7,
            push_retries=11,
            push_retry_interval=41,
            join_timeout=371
        )
        _conf.update(conf)
        return _server_config(tmp_path, pubkey, privkey, _conf)

    return _get_config


@pytest.fixture(scope='function')
def tmp_server_config(tmp_path_factory: pytest.TempPathFactory,
                      keypairgen: callable) -> callable:
    """Generate a full server config and config file."""

    def _get_config(**conf):
        tmp_path = tmp_path_factory.mktemp('server_config')
        privkey, _ = keypairgen()
        _, pubkey = keypairgen()
        config_path, _ = _server_config(tmp_path, pubkey, privkey, conf)
        return ServerConfig.load(config_path)

    return _get_config
