
import base64
import os
import re
from dataclasses import dataclass, field
from typing import Optional

from paramiko.ed25519key import Ed25519Key

from ... import DEFAULT_CLIENT_SOURCE_DIR, DEFAULT_USERNAME
from ...errors import ConfigError

PUBKEY_RE = re.compile(
    r'^(?:ssh-ed25519 +)?((?:[A-Za-z\d+/]{4}){17}'
    r'(?:[A-Za-z\d+/]{3}=|[A-Za-z\d+/]{2}==|[A-Za-z\d+/]{4})?)(?: .*)?$'
)


@dataclass
class ClientConnection:  # pylint: disable=too-many-instance-attributes
    """CertDeploy client connection config."""

    address: str
    """Client address or hostname."""
    domains: list[str]
    """Domains the client needs certs for (eg
    ``['www.example.com', 'example.com']``)
    """
    pubkey: str
    """The text of the public key of the client."""
    port: int = 22
    """The port the client or an SFTP server on the client host is listening on.
    """
    username: str = DEFAULT_USERNAME
    """The username to connect to the client with."""
    path: Optional[os.PathLike] = DEFAULT_CLIENT_SOURCE_DIR
    """The path on the client to sync the certs to."""
    needs_chain: bool = False
    """If `True` the client needs the ``chain.pem`` for the domains in
    `domains`.
    """
    needs_fullchain: bool = True
    """If `True` the client needs the ``fullchain.pem`` for the domains in
    `domains`.
    """
    needs_privkey: bool = True
    """If `True` the client needs the ``privkey.pem`` for the domains in
    `domains`.
    """
    pubkey_blob: Optional[Ed25519Key] = field(init=False)
    """The text of the public key formatted for `paramiko`. Set on instance
    creation.
    """

    def __post_init__(self):
        match = PUBKEY_RE.match(self.pubkey)
        if not match:
            raise ConfigError(f'Invalid value for `pubkey`: {self.pubkey}')
        self.pubkey_blob = Ed25519Key(
            data=base64.decodebytes(match.group(1).encode())
        )
