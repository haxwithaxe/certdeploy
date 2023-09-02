"""PKI data generation fixtures."""

import io
import pathlib
from dataclasses import dataclass
from typing import Callable

import paramiko
import pytest
from cryptography.hazmat.primitives import asymmetric, serialization

# Shared base names for private keys. Add `.pub` to make the public key name.
CLIENT_KEY_NAME = 'client_key'
SERVER_KEY_NAME = 'server_key'


@dataclass
class KeyPair:
    """A representation of a cryptographic key pair."""

    privkey_pem: str
    """The PEM formatted private key."""
    privkey_text: str
    """The decoded text of the private key."""
    pubkey_text: str
    """The decoded text of the public key."""
    privkey_name: str = 'privkey'
    """The default value for `name` in `privkey_file`."""
    pubkey_name: str = 'pubkey'
    """The default value for `name` in `pubkey_file`."""
    _path: pathlib.Path = None
    """The default value for `tmp_path` in `privkey_file` and `pubkey_file`.
    It can be set using `set_path`."""

    def privkey_file(self, tmp_path: pathlib.Path = None, name: str = None
                     ) -> pathlib.Path:
        """Write the private key to a file.

        Arguments:
            tmp_path (pathlib.Path, optional): The directory to write the
                private key file in. If `_path` has not been set this argument
                is not optional. Defaults to the value of `_path`.
            name (str, optional): The name to use for the file. If the
                `_privkey_name` has not been set this argument is not optional.
                Defaults to the value of `_privkey_name`.
        """
        name = name or self.privkey_name
        tmp_path = tmp_path or self._path
        filename = tmp_path.joinpath(self.privkey_name)
        filename.write_text(self.privkey_pem)
        return filename

    def pubkey_file(self, tmp_path: pathlib.Path = None, name: str = None
                    ) -> pathlib.Path:
        """Write the public key to a file.

        Arguments:
            tmp_path (pathlib.Path, optional): The directory to write the
                public key file in. If `_path` has not been set this argument
                is not optional. Defaults to the value of `_path`.
            name (str, optional): The name to use for the file. If the
                `_pubkey_name` has not been set this argument is not optional.
                Defaults to the value of `_pubkey_name`.
        """
        name = name or self.privkey_name
        tmp_path = tmp_path or self._path
        filename = tmp_path.joinpath(self.pubkey_name)
        filename.write_text(self.pubkey_text)
        return filename

    def update(self, path: pathlib.Path = None, privkey_name: str = None,
               pubkey_name: str = None):
        self._path = path if path else self._path
        self.privkey_name = privkey_name if privkey_name else self.privkey_name  # noqa: E501 readability
        self.pubkey_name = pubkey_name if pubkey_name else self.pubkey_name
        return self

    def __iter__(self):
        """Emulate the original output type."""
        return iter(tuple(self.privkey_text, self.pubkey_text))


def _keypairgen() -> KeyPair:
    """Generate a private and public key pair.

    Returns:
        KeyPair: A private key and a public key in a wrapper.
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
    return KeyPair(
        privkey_pem=privkey_pem.decode(),
        privkey_text=privkey.get_base64(),
        pubkey_text=openssh_pub.decode()
    )


@pytest.fixture(scope='function')
def pubkeygen() -> Callable[[], str]:
    """Return a public key string factory."""

    def _pubkeygen() -> str:
        """Return a freshly generated public key string."""
        return _keypairgen().pubkey_text

    return _pubkeygen


@pytest.fixture(scope='function')
def keypairgen() -> Callable[[], KeyPair]:
    """Return a key pair string factory.

    Returns:
        callable: Returns a `KeyPair` with a private key and a public key.
    """
    return _keypairgen
