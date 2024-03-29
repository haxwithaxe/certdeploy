"""CertDeploy Server client connection configs."""

import base64
import os
import re
from dataclasses import dataclass, field
from hashlib import sha1
from typing import Optional

from paramiko.ed25519key import Ed25519Key

from ... import DEFAULT_CLIENT_SOURCE_DIR, DEFAULT_USERNAME
from ...errors import ConfigInvalid, ConfigInvalidNumber
from ._validation import is_optional_int

# A regex to match an ed25519 public key
PUBKEY_RE = re.compile(
    r'^(?:ssh-ed25519 +)?((?:[A-Za-z\d+/]{4}){17}'
    r'(?:[A-Za-z\d+/]{3}=|[A-Za-z\d+/]{2}==|[A-Za-z\d+/]{4})?)(?: .*)?$'
)


@dataclass
class ClientConnection:
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
    push_retries: Optional[int] = None
    """The number of times to retry connecting to this client.

    * `None` lets the global `push_retries` config control this value.
    * `0` will cause the server to only try to push once (no retries).
    * Any other positive integer will cause the server to try to push certs
        to this client and retry as many as that many times before giving up.
    """
    push_retry_interval: Optional[int] = None
    """The interval to wait between retries for this client.

    * `None` lets the global `push_retry_interval` control this value.
    * `0` disables any delay between retries.
    * Any other positive integer is used as the number of seconds between
        attempts to push certs to this client.
    """
    pubkey_blob: Optional[Ed25519Key] = field(init=False)
    """The text of the public key formatted for `paramiko`. Set on instance
    creation.

    This is automatically generated when the configs are loaded.
    """
    hash: Optional[str] = field(init=False)
    """A hash of the client's user, address, and port.

    Used internally for indexing queues.
    """

    def __post_init__(self):
        """Validate configs.

        Raises:
            ConfigError: If any config option that is checked has something
                wrong.
        """
        # Validate public key
        match = PUBKEY_RE.match(self.pubkey)
        if not match:
            raise ConfigInvalid('pubkey', self.pubkey)
        self.pubkey_blob = Ed25519Key(
            data=base64.decodebytes(
                match.group(1).encode(),
            )
        )
        # Generate client connection hash
        self.hash = sha1(
            f'{self.username}{self.address}{self.port}'.encode()
        ).hexdigest()
        # Validate push_retry_interval
        if not is_optional_int(self.push_retry_interval, 0):
            raise ConfigInvalidNumber(
                'push_retry_interval', self.push_retry_interval, 'integer', ge=0
            )
        # Validate push_retries
        if not is_optional_int(self.push_retries, 0):
            raise ConfigInvalidNumber(
                'push_retries', self.push_retries, 'integer', ge=0
            )

    def __str__(self) -> str:
        """Return the client as it would be given to the SFTP client."""
        return f'{self.username}@[{self.address}]:{self.port}'
