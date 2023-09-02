
import base64
import os
import pathlib

import paramiko
import pytest
from fixtures.docker_container import CLIENT_SOURCE_DIR
from fixtures.keys import KeyPair
from paramiko.ed25519key import Ed25519Key


def _sftp_mkdir(sftp, path, mode=None):
    """Recursively make a remote directory if needed."""
    if path in ('', '/'):
        return
    mode = mode if mode is None else 0o700
    try:
        sftp.stat(path)
        return
    except FileNotFoundError:
        pass
    _sftp_mkdir(sftp, os.path.dirname(path), mode)
    sftp.mkdir(path, mode=mode)


@pytest.fixture()
def mock_server_push(keypairgen: callable, lineage_factory: callable,
                     tmp_path: pathlib.Path) -> tuple[KeyPair, callable]:
    """Return the server's pubkey and a function to push to a client."""
    default_server_keypair = keypairgen()

    def _push_to_client(
        client_path: pathlib.Path = None,
        lineage_name: str = None,
        client_config: dict = None,
        client_address: str = None,
        client_keypair: KeyPair = None,
        server_keypair: KeyPair = None,
        filenames: list[pathlib.Path] = None
    ):
        """Push arbitrarily named certs to a client."""
        client_path = client_path or pathlib.Path(CLIENT_SOURCE_DIR)
        server_keypair = server_keypair or default_server_keypair
        filenames = filenames or ['fullchain.pem', 'privkey.pem']
        lineage_dir = lineage_factory(lineage_name, filenames)
        cert_dir = client_path.joinpath(lineage_name)
        if not client_address:
            client_address = client_config['sftpd']['listen_address']
        if client_address == '0.0.0.0':
            client_address = '127.0.0.1'
        client_port = client_config['sftpd']['listen_port']
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
            sftp.put(str(lineage_dir.joinpath(filename)),
                     str(cert_dir.joinpath(filename)))
        sftp.close()
        ssh.close()

    return default_server_keypair, _push_to_client
