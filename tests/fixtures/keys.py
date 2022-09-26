
import io

import paramiko
import pytest
from cryptography.hazmat.primitives import asymmetric, serialization


def _keypairgen() -> tuple[str, str]:
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
    def _pubkeygen() -> str:
        return _keypairgen()[1]
    return _pubkeygen


@pytest.fixture(scope='function')
def keypairgen() -> callable:
    return _keypairgen
