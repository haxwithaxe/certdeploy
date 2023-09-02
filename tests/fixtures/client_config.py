"""Temporary client config fixtures."""

import pathlib
from typing import Any

import pytest
import yaml
from fixtures.keys import CLIENT_KEY_NAME, SERVER_KEY_NAME, KeyPair
from fixtures.utils import ConfigContext, get_free_port

from certdeploy.client.config import ClientConfig


def client_config_file(tmp_path: pathlib.Path, client_keypair: KeyPair = None,
                       server_keypair: KeyPair = None, sftpd: dict = None,
                       **conf: Any) -> ConfigContext:
    """Finish configuring the temporary client config.

    Arguments:
        tmp_path (pathlib.Path): Base directory for the config.
        sftpd (dict, optional): The `sftpd` config option gets special
            treatment.

    Keyword Arguments:
        conf: Key value pairs corresponding to
            `certdeploy.client.config.client.Config` arguments.

    Returns:
        ClientConfig: The client config with the given values.
    """
    src = tmp_path.joinpath('src')
    src.mkdir()
    dest = tmp_path.joinpath('dest')
    dest.mkdir()
    config_filename = tmp_path.joinpath('client.yml')
    # Non-default values for top level options
    config = dict(
        destination=str(dest),
        source=str(src),
        sftpd=sftpd or {}
    )
    if sftpd is not None and sftpd != {}:
        conf['sftpd'] = client_sftpd_config(tmp_path, client_keypair,
                                            server_keypair, **sftpd)
    config.update(conf)
    yaml.safe_dump(config, config_filename.open('w'))
    return ConfigContext(config_filename, config)


def client_sftpd_config(
    tmp_path: pathlib.Path = None,
    client_keypair: KeyPair = None,
    server_keypair: KeyPair = None,
    listen_port: int = None,
    **conf: Any
) -> dict:
    if not client_keypair.path:
        client_keypair.update(path=tmp_path)
    if not client_keypair.privkey_name:
        client_keypair.update(privkey_name=SERVER_KEY_NAME)
    if not client_keypair.pubkey_name:
        client_keypair.update(pubkey_name=f'{SERVER_KEY_NAME}.pub')
    config = dict(
        listen_port=listen_port if listen_port else get_free_port(),
        privkey_filename=f'/etc/certdeploy/{CLIENT_KEY_NAME}',
    )
    if client_keypair:
        config['privkey_filename'] = str(client_keypair.privkey_file())
    if server_keypair and 'server_pubkey_file' not in conf:
        config['server_pubkey'] = server_keypair.pubkey_text
    config.update(conf)
    return config


@pytest.fixture(scope='function')
def tmp_client_sftpd_config(free_port: callable) -> callable:
    return client_sftpd_config


@pytest.fixture(scope='function')
def tmp_client_config_file(tmp_path_factory: pytest.TempPathFactory
                           ) -> callable:
    """Return a temporary client config constructor."""

    def _tmp_client_config_file(
        tmp_path: pathlib.Path = None,
        client_keypair: KeyPair = None,
        server_keypair: KeyPair = None,
        **conf: Any
    ) -> ConfigContext:
        """Finish configuring the temporary client config.

        Keyword Arguments:
            conf: Key value pairs corresponding to
                `certdeploy.client.config.client.Config` arguments.
        Returns:
            pathlib.Path, dict: The path of the client config and the `dict`
                used to create it.
        """
        # Non-default values for top level options
        config = dict(
            sftpd={},
            systemd_exec='test systemd_exec value',
            systemd_timeout=42,
            docker_url='test docker_url value',  # Use the local socket
            update_services=[],
            update_delay='11s'
        )
        config.update(conf)
        return client_config_file(
            tmp_path or tmp_path_factory.mktemp('tmp_client_config_file'),
            client_keypair=client_keypair,
            server_keypair=server_keypair,
            **config
        )

    return _tmp_client_config_file


@pytest.fixture(scope='function')
def tmp_client_config(tmp_path_factory: pytest.TempPathFactory) -> callable:
    """Return a temporary client config constructor."""

    def _tmp_client_config(client_keypair: KeyPair = None,
                           server_keypair: KeyPair = None, **conf: Any
                           ) -> ClientConfig:
        """Finish configuring the temporary client config.

        Arguments:
            client_keypair (KeyPair, optional): The key pair for the
                CertDeploy client.
            server_keypair (KeyPair, optional): The key pair for the CertDeploy
                server.

        Keyword Arguments:
            conf: Key value pairs corresponding to
                `certdeploy.client.config.client.Config` arguments.

        Returns:
            ClientConfig: The client config with the given values.
        """
        tmp_path = tmp_path_factory.mktemp('client_config')
        config_context = client_config_file(tmp_path, client_keypair,
                                            server_keypair, **conf)
        return ClientConfig.load(config_context.config_path)

    return _tmp_client_config
