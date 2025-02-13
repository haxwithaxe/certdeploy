"""Temporary client config fixtures."""

import pathlib
from typing import Any, Callable

import pytest
import yaml
from fixtures.keys import CLIENT_KEY_NAME, KeyPair
from fixtures.utils import ConfigContext, get_free_port

from certdeploy.client.config import ClientConfig


def client_config_file(
    tmp_path: pathlib.Path,
    client_keypair: KeyPair = None,
    server_keypair: KeyPair = None,
    sftpd: dict = None,
    **conf: Any,
) -> ConfigContext:
    """Finish configuring the temporary client config.

    Arguments:
        tmp_path: Base directory for the config.
        client_keypair: The CertDeploy client's key pair.
        server_keypair: The CertDeploy server's key pair.
        sftpd: The `sftpd` config option gets special treatment. If this is
            `None` or `{}` (empty `dict`) Nothing will be done to it. Otherwise
            it's run through `client_sftp_config` to give it some basic values.

    Keyword Arguments:
        conf: Key value pairs corresponding to
            `certdeploy.client.config.client.Config` arguments.

    Returns:
        The client config with the given values or minimum values.
    """
    src = tmp_path.joinpath('src')
    src.mkdir()
    dest = tmp_path.joinpath('dest')
    dest.mkdir()
    config_filename = tmp_path.joinpath('client.yml')
    # Non-default values for top level options
    config = dict(destination=str(dest), source=str(src), sftpd=sftpd or {})
    if sftpd is not None and sftpd != {}:
        conf['sftpd'] = client_sftpd_config(
            tmp_path, client_keypair, server_keypair, **sftpd
        )
    config.update(conf)
    yaml.safe_dump(config, config_filename.open('w'))
    return ConfigContext(
        config_filename,
        config,
        client_keypair,
        server_keypair,
    )


def client_sftpd_config(
    tmp_path: pathlib.Path = None,
    client_keypair: KeyPair = None,
    server_keypair: KeyPair = None,
    listen_address: str = '127.0.0.1',
    listen_port: int = None,
    **conf: Any,
) -> dict:
    """Finish configuring the temporary client SFTPD config.

    Arguments:
        tmp_path: Base directory for the config.
        client_keypair: The CertDeploy client's key pair.
        server_keypair: The CertDeploy server's key pair.
        listen_port: The port for SFTPD to listen on. Defaults
            to a random port above 1024.

    Keyword Arguments:
        conf: Key value pairs corresponding to
            `certdeploy.client.config.client.Config` arguments.

    Returns:
        The client SFTPD config with the given values or minimum values.
    """
    if not listen_port:
        listen_port = get_free_port(address=listen_address)
    config = dict(
        listen_address=listen_address,
        listen_port=listen_port,
        privkey_filename=f'/etc/certdeploy/{CLIENT_KEY_NAME}',
    )
    if client_keypair:
        if not client_keypair.path:
            client_keypair.update(path=tmp_path)
        if not client_keypair.privkey_name:
            client_keypair.update(privkey_name=CLIENT_KEY_NAME)
        if not client_keypair.pubkey_name:
            client_keypair.update(pubkey_name=f'{CLIENT_KEY_NAME}.pub')
        config['privkey_filename'] = str(client_keypair.privkey_file())
    if server_keypair and 'server_pubkey_filename' not in conf:
        config['server_pubkey'] = server_keypair.pubkey_text
    config.update(conf)
    return config


@pytest.fixture(scope='function')
def tmp_client_sftpd_config(
    free_port: callable,
) -> Callable[[pathlib.Path, KeyPair, KeyPair, int, ...], dict]:
    """Return a `sftpd` config section factory."""
    return client_sftpd_config


@pytest.fixture(scope='function')
def tmp_client_config_file(
    tmp_path_factory: pytest.TempPathFactory, keypairgen: callable
) -> Callable[[pathlib.Path, KeyPair, KeyPair, ...], ConfigContext]:
    """Return a temporary client config constructor."""

    def _tmp_client_config_file(
        tmp_path: pathlib.Path = None,
        client_keypair: KeyPair = None,
        server_keypair: KeyPair = None,
        **conf: Any,
    ) -> ConfigContext:
        """Finish configuring the temporary client config.

        Arguments:
            tmp_path: The temporary directory to use in this function. Defaults
                to a freshly generated temporary directory.
            client_keypair: The key pair for the CertDeploy client. Defaults to
                a freshly generated key pair.
            server_keypair: The key pair for the CertDeploy server. Defaults to
                a freshly generated key pair.

        Keyword Arguments:
            conf: Key value pairs corresponding to
                `certdeploy.client.config.client.Config` arguments.
        Returns:
            The path of the client config and the `dict` used to create it.
        """
        tmp_path = tmp_path or tmp_path_factory.mktemp('tmp_client_config_file')
        client_keypair = client_keypair or keypairgen()
        server_keypair = server_keypair or keypairgen()
        # Non-default values for top level options except log_filename
        #   The log output to stdout/stderr is useful
        config = dict(
            sftpd={},
            systemd_exec='test systemd_exec value',
            rc_service_exec='test rc_service_exec value',
            docker_timeout=19,
            init_timeout=42,
            script_timeout=17,
            docker_url='test docker_url value',  # Use the local socket
            update_services=[],
            update_delay='11s',
            log_level='DEBUG',
        )
        config.update(conf)
        return client_config_file(
            tmp_path,
            client_keypair=client_keypair,
            server_keypair=server_keypair,
            **config,
        )

    return _tmp_client_config_file


@pytest.fixture(scope='function')
def tmp_client_config(
    tmp_path_factory: pytest.TempPathFactory, keypairgen: callable
) -> Callable[[KeyPair, KeyPair, ...], ClientConfig]:
    """Return a temporary client config factory."""

    def _tmp_client_config(
        tmp_path: pathlib.Path = None,
        client_keypair: KeyPair = None,
        server_keypair: KeyPair = None,
        **conf: Any,
    ) -> ClientConfig:
        """Finish configuring the temporary client config.

        Arguments:
            tmp_path: The temporary directory path to put files in.
            client_keypair: The key pair for the CertDeploy client.
            server_keypair: The key pair for the CertDeploy server.

        Keyword Arguments:
            conf: Key value pairs corresponding to
                `certdeploy.client.config.client.Config` arguments.

        Returns:
            The client config with the given values.
        """
        tmp_path = tmp_path or tmp_path_factory.mktemp('tmp_client_config')
        client_keypair = client_keypair or keypairgen()
        server_keypair = server_keypair or keypairgen()
        config_context = client_config_file(
            tmp_path, client_keypair, server_keypair, **conf
        )
        return ClientConfig.load(config_context.config_path)

    return _tmp_client_config
