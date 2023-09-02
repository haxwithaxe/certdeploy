
import base64
import pathlib
from dataclasses import dataclass

import paramiko
import pytest
from fixtures.docker_container import CLIENT_SOURCE_DIR
from fixtures.keys import CLIENT_KEY_NAME, SERVER_KEY_NAME, KeyPair
from paramiko.ed25519key import Ed25519Key

from certdeploy.server.server import _sftp_mkdir


@dataclass
class MockPushContext:

    pusher: callable = None
    server_keypair: KeyPair = None
    client_keypair: KeyPair = None
    filenames: list[str] = None
    client_address: str = None


def _push_to_client(
    client_path: pathlib.Path,
    client_address: str,
    client_port: int,
    client_keypair: KeyPair,
    server_keypair: KeyPair,
    lineage_path: pathlib.Path,
    filenames: list[pathlib.Path]
):
    """Push arbitrarily named certs to a client."""
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
def mock_server_push(keypairgen: callable, lineage_factory: callable,
                     tmp_path: pathlib.Path) -> MockPushContext:
    """Return the server's pubkey and a function to push to a client."""
    context = MockPushContext()

    def _mock_server_push(
        client_config: dict,
        client_path: pathlib.Path = None,
        client_address: str = None,
        client_keypair: KeyPair = None,
        server_keypair: KeyPair = None,
        lineage_name: str = None,
        filenames: list[pathlib.Path] = None
    ):
        """Push arbitrarily named certs to a client."""
        ## Reconsile the variables
        # Calling out the places where things are added to the context so they
        #   don't get lost in the noise.
        client_path = client_path or pathlib.Path(CLIENT_SOURCE_DIR)
        default_client_keypair = keypairgen().update(
            path=tmp_path,
            privkey_name=CLIENT_KEY_NAME
        )
        client_keypair = client_keypair or default_client_keypair
        # Add client_keypair to the context
        context.client_keypair = client_keypair
        default_server_keypair = keypairgen().update(
            path=tmp_path,
            privkey_name=SERVER_KEY_NAME
        )
        server_keypair = server_keypair or default_server_keypair
        # Add server_keypair to the context
        context.server_keypair = server_keypair
        filenames = filenames or ['fullchain.pem', 'privkey.pem']
        # Add filenames to the context
        context.filenames = filenames
        lineage_path = lineage_factory(lineage_name, context.filenames)
        if not client_address:
            client_address = client_config['sftpd']['listen_address']
        if context.client_address == '0.0.0.0':
            client_address = '127.0.0.1'
        # Add client_address to the context
        context.client_address = client_address
        client_port = client_config['sftpd']['listen_port']
        ## Do the push
        _push_to_client(client_path, client_address, client_port,
                        client_keypair, server_keypair, lineage_path,
                        filenames)

    context.pusher = _mock_server_push
    return context
