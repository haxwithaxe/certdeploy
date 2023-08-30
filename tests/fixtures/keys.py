"""PKI data generation fixtures."""

import io
import pathlib

import paramiko
import pytest
from cryptography.hazmat.primitives import asymmetric, serialization


def _keypairgen() -> tuple[str, str]:
    """Generate a pair of private and public key strings.

    Returns:
        str, str: First the private key then the public key.
    """
    keypair = asymmetric.ed25519.Ed25519PrivateKey.generate()
    privkey_pem = keypair.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption()
    )
    privkey_io = io.StringIO(privkey_pem.decode())
    privkey = paramiko.ed25519key.Ed25519Key.from_private_key(privkey_io)
    pubkey = keypair.public_key()
    openssh_pub = pubkey.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH
    )
    return privkey.get_base64(), openssh_pub.decode()


@pytest.fixture(scope='function')
def pubkeygen() -> callable:
    """Return a pubkey string factory."""

    def _pubkeygen() -> str:
        """Return a freshly generated public key string."""
        return _keypairgen()[1]

    return _pubkeygen


@pytest.fixture(scope='function')
def keypairgen() -> callable:
    """Return a key pair string factory.

    Returns:
        str, str: The private key then the public key.
    """
    return _keypairgen


@pytest.fixture(scope='function')
def keypairgen_privkey_file(tmp_path: pathlib.Path) -> callable:
    """Return a key pair with private key file factory."""

    def _with_privkey_file() -> tuple[str, str, pathlib.Path]:
        """Generate a key pair with a private key file.

        Returns:
            str, str, pathlib.Path: First the private key string. Second the
                public key string. Third the path of the private key file.
        """
        privkey, pubkey = _keypairgen()
        privkey_path = tmp_path.joinpath('privkey')
        privkey_path.write_bytes(privkey.encode())
        return privkey, pubkey, privkey_path

    return _with_privkey_file
