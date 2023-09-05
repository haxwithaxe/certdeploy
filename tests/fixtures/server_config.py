"""Fixtures for generating temporary CertDeploy server configs."""

import pathlib
from typing import Any, Callable

import pytest
import yaml
from fixtures.keys import SERVER_KEY_NAME, KeyPair
from fixtures.utils import ConfigContext

from certdeploy.server.config import ServerConfig


def client_conn_config(client_keypair: KeyPair, **conf: Any) -> dict:
    """Generate a minimal dict to pass as a client connection config.

    Arguments:
        client_keypair: The client key pair.
        conf: A dict of configs to be eventually passed to `ClientConnection`.

    Returns:
        A minimal client connection config updated with `conf`.
    """
    _conf = dict(
        address='test_client_address',
        domains=['test.example.com'],
        pubkey=client_keypair.pubkey_text
    )
    if conf:
        _conf.update(conf)
    return _conf


@pytest.fixture(scope='function')
def client_conn_config_factory(keypairgen: Callable[[], KeyPair]
                               ) -> Callable[[KeyPair, ...], dict]:
    """Generate dicts to go into the `client_configs` section."""

    def _client_conn_config_factory(client_keypair: KeyPair = None,
                                    **conf: Any) -> dict:
        """Return a `dict` representing a client connection config.

        Arguments:
            client_keypair: The client key pair. Defaults to a freshly generated
                `KeyPair`.

        Keyword Arguments:
            conf: Key value pairs to be included in or override the values to
                be passed to `ClientConnection`.
        """
        client_keypair = client_keypair or keypairgen()
        return client_conn_config(client_keypair, **conf)

    return _client_conn_config_factory


def server_config_file(tmp_path: pathlib.Path, client_keypair: KeyPair,
                       server_keypair: KeyPair, **conf: Any) -> ConfigContext:
    """Generate a minimal CertDeploy server config updated with `conf`.

    Updates `server_keypair` with `tmp_path` as the path and sets
    `server_keypair.privkey_name` to `SERVER_KEY_NAME` if it isn't already set.

    Arguments:
        tmp_path: The temporary directory to put the config file and private key
            file in.
        client_keypair: A keypair for the CertDeploy client.
        server_keypair: A keypair for the CertDeploy server.

    Keyword Arguments:
        conf: A `dict` of arguments to eventually be passed to `ServerConfig`.

    Returns:
        A filled out config context.
    """
    queue_dir = tmp_path.joinpath('queue')
    queue_dir.mkdir()
    server_keypair.update(path=tmp_path)
    if not server_keypair.privkey_name:
        server_keypair.update(privkey_name=SERVER_KEY_NAME)
    config_path = tmp_path.joinpath('server.yml')
    config = dict(
        privkey_filename=str(server_keypair.privkey_file()),
        client_configs=[client_conn_config(client_keypair=client_keypair)],
        # Has to be a real dir writable by the test user
        queue_dir=str(queue_dir)
    )
    config.update(conf)
    yaml.safe_dump(config, config_path.open('w'))
    return ConfigContext(config_path, config, client_keypair, server_keypair)


@pytest.fixture(scope='function')
def tmp_server_config_file(
    tmp_path_factory: pytest.TempPathFactory,
    keypairgen: Callable[[], KeyPair]
) -> Callable[[pathlib.Path, KeyPair, KeyPair, ...], ConfigContext]:
    """Generate a full CertDeploy server config and matching config file.

    This sets all the possible values to non-default values to help test the
    ServerConfig.
    """

    def _tmp_server_config_file(
        tmp_path: pathlib.Path = None,
        client_keypair: KeyPair = None,
        server_keypair: KeyPair = None,
        **conf: Any
    ) -> ConfigContext:
        """Generate a full CertDeploy server config and matching config file.

        Note:
            This sets all the possible values to non-default values to help
            test `ServerConfig`. The `ServerConfig` tests are the only place
            this fixture should be used.

        Arguments:
            tmp_path: A temporary base directory. Defaults to a new temporary
                directory.
            client_keypair: A key pair for the CertDeploy client. Defaults to a
                freshly generated `KeyPair`.
            server_keypair: A key pair for the CertDeploy server. Defaults to a
                freshly generated `KeyPair`.

        Keyword Arguments:
            conf: Key value pairs corresponding to the possible arguments of
                `ServerConfig`.

        Returns:
            ConfigContext: A filled out context.
        """
        tmp_path = tmp_path or tmp_path_factory.mktemp('server_config')
        server_keypair = server_keypair or keypairgen()
        client_keypair = client_keypair or keypairgen()
        config = dict(
            fail_fast=False,
            log_level='DEBUG',
            sftp_log_level='DEBUG',
            sftp_log_filename='/dev/null',
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
        config.update(conf)
        return server_config_file(tmp_path, client_keypair, server_keypair,
                                  **config)

    return _tmp_server_config_file


@pytest.fixture(scope='function')
def tmp_server_config(
    tmp_path_factory: pytest.TempPathFactory,
    keypairgen: Callable[[], KeyPair]
) -> Callable[[pathlib.Path, KeyPair, KeyPair, ...], ServerConfig]:
    """Return a `ServerConfig` factory."""

    def _tmp_server_config(
        tmp_path: pathlib.Path = None,
        client_keypair: KeyPair = None,
        server_keypair: KeyPair = None,
        **conf: Any
    ) -> ServerConfig:
        """Return a minimal `ServerConfig` with the additions of `conf`.

        Arguments:
            tmp_path: A temporary base directory. Defaults to a new temporary
                directory.
            client_keypair: A key pair for the CertDeploy client. Defaults to a
                freshly generated `KeyPair`.
            server_keypair: A key pair for the CertDeploy server. Defaults to a
                freshly generated `KeyPair`.

        Keyword Arguments:
            conf: Key value pairs corresponding to the possible arguments of
                `ServerConfig`.
        """
        tmp_path = tmp_path or tmp_path_factory.mktemp('server_config')
        client_keypair = client_keypair or keypairgen()
        server_keypair = server_keypair or keypairgen()
        context = server_config_file(tmp_path, client_keypair,
                                     server_keypair, **conf)
        return ServerConfig.load(context.config_path)

    return _tmp_server_config
