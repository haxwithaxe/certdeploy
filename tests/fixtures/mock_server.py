"""Mock CertDeploy server fixtures and utilities."""

import base64
import pathlib
from dataclasses import dataclass
from typing import Callable, Union

import paramiko
import pytest
from fixtures.docker_container import ContainerInternalPaths
from fixtures.keys import CLIENT_KEY_NAME, SERVER_KEY_NAME, KeyPair
from paramiko.ed25519key import Ed25519Key

from certdeploy.client.config import ClientConfig
from certdeploy.server.server import _sftp_mkdir


@dataclass
class MockPushContext:
    """A context wrapper for `mock_push_server`."""

    push: Callable[[], None]
    client_address: str
    client_keypair: KeyPair
    server_keypair: KeyPair
    filenames: list[str]


def _push_to_client(
    client_path: pathlib.Path,
    client_address: str,
    client_port: int,
    client_keypair: KeyPair,
    server_keypair: KeyPair,
    lineage_path: pathlib.Path,
    filenames: list[pathlib.Path]
):
    """Push arbitrarily named certs to a client.

    Arguments:
        client_path: The path on the client to dump the lineage in.
        client_address: The listen address of the CertDeploy client.
        client_port: The listen port of the CertDeploy client.
        client_keypair: The key pair for the CertDeploy client.
        server_keypair: The key pair for the CertDeploy server.
        lineage_path: The local path of the lineage.
        filenames: A list of filenames to transfer from `lineage_path` to
            `client_path`
    """
    cert_dir = client_path.joinpath(lineage_path.name)
    ssh = paramiko.client.SSHClient()
    if client_port == 22:
        hostkey_name = client_address
    else:
        hostkey_name = f'[{client_address}]:{client_port}'
    client_pubkey_blob = Ed25519Key(
        data=base64.decodebytes(
            client_keypair.pubkey_text.split()[1].encode('utf-8')
        )
    )
    ssh.get_host_keys().add(hostkey_name, 'ssh-ed25519', client_pubkey_blob)
    # Set the safest policy by default
    ssh.set_missing_host_key_policy(paramiko.client.RejectPolicy)
    ssh.connect(hostname=client_address, port=client_port,
                username='certdeploy',
                key_filename=str(server_keypair.privkey_file()))
    sftp = ssh.open_sftp()
    _sftp_mkdir(sftp, str(cert_dir))
    for filename in filenames:
        sftp.put(str(lineage_path.joinpath(filename)),
                 str(cert_dir.joinpath(filename)))
    sftp.close()
    ssh.close()


@pytest.fixture()
def mock_server_push(
    keypairgen: Callable[[], KeyPair],
    lineage_factory: Callable[[str, list[str]], pathlib.Path],
    tmp_path: pathlib.Path
) -> Callable[[dict, pathlib.Path, str, KeyPair, KeyPair, str,
               list[pathlib.Path]], MockPushContext]:
    """Return a mock CertDeploy server push context factory."""

    def _mock_server_push(
        client_config: Union[ClientConfig, dict],
        client_path: pathlib.Path = None,
        client_address: str = None,
        client_keypair: KeyPair = None,
        server_keypair: KeyPair = None,
        lineage_name: str = None,
        filenames: list[pathlib.Path] = None
    ) -> MockPushContext:
        """Prepare to push arbitrarily named certs to a client.

        Arguments:
            client_config: CertDeploy client config `dict`.
            client_path: The path on the client to dump the lineage in.
                Defaults to a new temporary directory.
            client_address: The listen address of the CertDeploy client.
                Defaults to the configured SFTPD `listen_address`.
            client_port: The listen port of the CertDeploy client. Defaults to
                the configured SFTPD `listen_port`.
            client_keypair: The key pair for the CertDeploy client. Defaults to
                a freshly generated `KeyPair`.
            server_keypair: The key pair for the CertDeploy server. Defaults to
                a freshly generated `KeyPair`.
            lineage_name: The name (not the path) of the lineage to generate.
                Defaults to `'test.example.com'`.
            filenames: A list of filenames to transfer from `lineage_path` to
                `client_path`. Defaults to `['fullchain.pem', 'privkey.pem']`.

        Returns:
            A context object with the pusher function, key pairs, lineage
            filenames, and client address.
        """
        ## Reconcile the variables
        # Calling out the places where things are added to the context so they
        #   don't get lost in the noise.
        client_path = client_path or ContainerInternalPaths.source
        default_client_keypair = keypairgen().update(
            path=tmp_path,
            privkey_name=CLIENT_KEY_NAME
        )
        client_keypair = client_keypair or default_client_keypair
        default_server_keypair = keypairgen().update(
            path=tmp_path,
            privkey_name=SERVER_KEY_NAME
        )
        server_keypair = server_keypair or default_server_keypair
        filenames = filenames or ['fullchain.pem', 'privkey.pem']
        lineage_path = lineage_factory(lineage_name or 'test.example.com',
                                       filenames)
        if isinstance(client_config, dict):
            client_config = ClientConfig(**client_config)
        if not client_address:
            client_address = client_config.sftpd_config.listen_address
        if client_address == '0.0.0.0':
            client_address = '127.0.0.1'
        client_port = client_config.sftpd_config.listen_port

        def _pusher():
            _push_to_client(client_path, client_address, client_port,
                            client_keypair, server_keypair, lineage_path,
                            filenames)

        context = MockPushContext(
            push=_pusher,
            client_keypair=client_keypair,
            server_keypair=server_keypair,
            filenames=filenames,
            client_address=client_address
        )
        return context

    return _mock_server_push
