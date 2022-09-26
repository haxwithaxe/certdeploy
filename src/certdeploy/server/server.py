
import os
import socket

import paramiko
from paramiko.ssh_exception import NoValidConnectionsError, SSHException

from .. import format_error
from ..errors import CertDeployError
from . import log
from .config import ServerConfig
from .config.client import ClientConnection


def _sftp_mkdir(sftp, path, mode=None):
    """Recursively make a remote directory if needed."""
    log.debug('_sftp_mkdir: path=%s, mode=%s', path, mode)
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


class Server:
    """Serve updated tls certs to clients.

    Arguments:
        config (Config): Server config.

    """

    def __init__(self, config: ServerConfig):
        self._config = config

    def _sync_client(self, client: ClientConnection, lineage: os.PathLike):
        cert_dir = os.path.join(client.path, os.path.basename(lineage))
        ssh = paramiko.client.SSHClient()
        if client.port == 22:
            hostkey_name = client.address
        else:
            hostkey_name = f'[{client.address}]:{client.port}'
        ssh.get_host_keys().add(hostkey_name, 'ssh-ed25519', client.pubkey_blob)
        # Set the safest policy by default
        ssh.set_missing_host_key_policy(paramiko.client.RejectPolicy)
        ssh.connect(hostname=client.address, port=client.port,
                    username=client.username,
                    key_filename=self._config.privkey_filename)
        sftp = ssh.open_sftp()
        _sftp_mkdir(sftp, cert_dir)
        if client.needs_chain:
            log.debug('Copying %s to %s',
                      os.path.join(lineage, 'chain.pem'),
                      os.path.join(cert_dir, 'chain.pem'))
            sftp.put(os.path.join(lineage, 'chain.pem'),
                     os.path.join(cert_dir, 'chain.pem'))
        if client.needs_fullchain:
            log.debug('Copying %s to %s',
                      os.path.join(lineage, 'fullchain.pem'),
                      os.path.join(cert_dir, 'fullchain.pem'))
            sftp.put(os.path.join(lineage, 'fullchain.pem'),
                     os.path.join(cert_dir, 'fullchain.pem'))
        if client.needs_privkey:
            log.debug('Copying %s to %s',
                      os.path.join(lineage, 'privkey.pem'),
                      os.path.join(cert_dir, 'privkey.pem'))
            sftp.put(os.path.join(lineage, 'privkey.pem'),
                     os.path.join(cert_dir, 'privkey.pem'))
        sftp.close()

    def sync(self, lineage: os.PathLike, domains: list[str]):
        """Synchronize clients that need updated domains."""
        for client in self._config.clients:
            for domain in domains:
                if domain in client.domains:
                    try:
                        self._sync_client(client, lineage)
                    except CertDeployError as err:
                        if self._config.fail_fast:
                            raise
                        log.error('Error syncing with %s:%s: %s',
                                  client.address, client.port,
                                  format_error(err), exc_info=err)
                    except (SSHException, NoValidConnectionsError,
                            socket.gaierror) as err:
                        if self._config.fail_fast:
                            raise
                        log.error('Error connecting to %s: %s: %s',
                                  client.address, client.port,
                                  format_error(err), exc_info=err)
                    break
