"""A daemon for accepting and installing certs from a CertDeploy server."""

import datetime
import os
import socket
import threading
import time

import paramiko

from . import log
from .config import ClientConfig
from .config.client import SFTPDConfig
from .deploy import deploy
from .errors import CertDeployError
from .update import update_services

DEFAULT_FILE_MODE = 0o600
# This acts like the sleep interval for the while True loop in
#  DeployServer.serve_forever
#  Increasing it makes errors in the update thread raise later.
#  Decreasing it makes the loop go faster and increases CPU load.
SOCKET_TIMEOUT = 1


class SSHServer(paramiko.ServerInterface):
    """Base SSH server to hand off SFTP connections.

    Attributes:
        valid_username (str): The username that is valid for login.
        valid_public_key (paramiko.PublicBlob): The server's public key.

    Arguments:
        config (ClientConfig): The CertDeploy client config.
        args (list[Any], optional): Passthrough positional arguments to the
            parent class.

    Keyword Arguments:
        kwargs (dict[Any, Any]): Passthrough keyword arguments to the parent
            class.
    """

    def __init__(self, config, *args, **kwargs):  # noqa: D107
        super().__init__(*args, **kwargs)
        self.valid_username = config.sftpd_config.username
        # Key is in the config file
        if config.sftpd_config.server_pubkey:
            self.valid_public_key = paramiko.PublicBlob.from_string(
                config.sftpd_config.server_pubkey
            )
        # Key is on disk
        if config.sftpd_config.server_pubkey_filename:
            self.valid_public_key = paramiko.PublicBlob.from_file(
                config.sftpd_config.server_pubkey_filename
            )

    def check_auth_password(self, username, password):
        """Override parent method to always deny password authentication."""
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        """Verify username and public key combination."""
        if (
            username == self.valid_username
            and key.asbytes() == self.valid_public_key.key_blob
        ):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        """Always allow channel requests."""  # noqa: D401
        return paramiko.OPEN_SUCCEEDED

    def get_allowed_auths(self, username):
        """List availble authentication mechanisms."""
        return 'publickey'


class SFTPHandle(paramiko.SFTPHandle):
    """SFTP file handle."""

    def stat(self):
        """Return stat data or error info for the `self.readfile`."""
        try:
            return paramiko.SFTPAttributes.from_stat(
                os.fstat(self.readfile.fileno()),
            )
        except OSError as err:
            return paramiko.SFTPServer.convert_errno(err.errno)

    def chattr(self, attr):
        """Set attributes for `self.filename`."""
        # python doesn't have equivalents to fchown or fchmod, so we have to
        # use the stored filename
        try:
            paramiko.SFTPServer.set_file_attr(self.filename, attr)
            return paramiko.SFTP_OK
        except OSError as err:
            return paramiko.SFTPServer.convert_errno(err.errno)


class StubSFTPServer(paramiko.SFTPServerInterface):
    """SFTPServer stub.

    Implements just the parts required to get certificates from the CertDeploy
    server. Also drops actions on paths outside of the upload directory.
    """

    _working_dir = None

    def _realpath(self, path):
        """Return the absolute, canonicalized path if `path`.

        Only if `path` is within the working directory. Otherwise return `None`.
        """
        # This isn't a general purpose SFTP server so sanitizing the path a
        #   little.
        path = path.replace('../', '/')
        if os.path.isabs(path):
            if path.startswith(self._working_dir):
                return self.canonicalize(path)
            return None  # Don't allow access outside of the target dir
        return self.canonicalize(os.path.join(self._working_dir, path))

    def list_folder(self, path):
        """List the contents of `path`."""
        log.debug('list_folder: path=%s', path)
        path = self._realpath(path)
        if not path:
            return paramiko.SFTP_PERMISSION_DENIED
        try:
            folder = []
            file_list = os.listdir(path)
            for filename in file_list:
                attr = paramiko.SFTPAttributes.from_stat(
                    os.stat(os.path.join(path, filename))
                )
                attr.filename = filename
                folder.append(attr)
            return folder
        except OSError as err:
            return paramiko.SFTPServer.convert_errno(err.errno)

    def stat(self, path):
        """Return stat data or error info for the `path`."""
        log.debug('stat: path=%s', path)
        path = self._realpath(path)
        if not path:
            return paramiko.SFTP_PERMISSION_DENIED
        try:
            return paramiko.SFTPAttributes.from_stat(os.stat(path))
        except OSError as err:
            return paramiko.SFTPServer.convert_errno(err.errno)

    def open(self, path, flags, attr):
        """Open `path` for reading or writing."""
        log.debug('open: path=%s, flags=%s, attr=%s', path, flags, attr)
        path = self._realpath(path)
        if not path:
            return paramiko.SFTP_PERMISSION_DENIED
        try:
            binary_flag = getattr(os, 'O_BINARY', 0)
            flags |= binary_flag
            mode = getattr(attr, 'st_mode', None)
            if mode is not None:
                file_desc_0 = os.open(path, flags, mode)
            else:
                # os.open() defaults to 0777 which is
                # an odd default mode for files
                file_desc_0 = os.open(path, flags, DEFAULT_FILE_MODE)
                log.debug(
                    'open: open %s with flags=%s and mode=%s ' '(default mode)',
                    path,
                    flags,
                    DEFAULT_FILE_MODE,
                )
        except OSError as err:
            log.debug(
                'open: failed to open %s with flags=%s and mode=%s '
                '(default mode)',  # fmt: skip
                path,
                flags,
                DEFAULT_FILE_MODE,
            )
            return paramiko.SFTPServer.convert_errno(err.errno)
        if flags & os.O_CREAT and attr is not None:
            attr._flags &= ~attr.FLAG_PERMISSIONS
            paramiko.SFTPServer.set_file_attr(path, attr)
        if flags & os.O_WRONLY:
            if flags & os.O_APPEND:
                mode = 'ab'
            else:
                mode = 'wb'
        elif flags & os.O_RDWR:
            if flags & os.O_APPEND:
                mode = 'a+b'
            else:
                mode = 'r+b'
        else:
            # O_RDONLY (== 0)
            mode = 'rb'
        try:
            file_desc = os.fdopen(file_desc_0, mode)
            log.debug('open: fdopen %s with mode=%s', path, mode)
        except OSError as err:
            log.debug('open: failed to fdopen %s with mode=%s', path, mode)
            return paramiko.SFTPServer.convert_errno(err.errno)
        file_obj = SFTPHandle(flags)
        file_obj.filename = path
        file_obj.readfile = file_desc
        file_obj.writefile = file_desc
        return file_obj

    def mkdir(self, path, attr):
        """Make a directory (`path`) with attributes (`attr`)."""
        log.debug('mkdir: path=%s, attr=%s', path, attr)
        path = self._realpath(path)
        if not path:
            return paramiko.SFTP_PERMISSION_DENIED
        try:
            os.mkdir(path)
            if attr is not None:
                paramiko.SFTPServer.set_file_attr(path, attr)
        except OSError as err:
            return paramiko.SFTPServer.convert_errno(err.errno)
        return paramiko.SFTP_OK


class _Update(threading.Thread):
    """Service update worker thread.

    Arguments:
        config: CertDeploy client config.
        update_func: The function to use to update services.
    """

    min_wait_seconds: int = 1
    """The interval to wait between checks for time to update in seconds"""

    def __init__(self, config: ClientConfig, update_func: callable):  # noqa: D107,E501
        threading.Thread.__init__(self, daemon=True)
        self._config: ClientConfig = config
        self.update_func: callable = update_func
        self._update_time: datetime.datetime = None
        self._exception: Exception = None

    def reset_update_time(self):
        """Reset the delay of the execution of the update.

        Resets the delay to "now" plus the delay interval.
        """
        delta = datetime.timedelta(seconds=self._config.update_delay_seconds)
        now = datetime.datetime.now()
        log.debug(
            'Reset execution time from %s to %s',
            self._update_time,
            (now + delta),
        )
        self._update_time = now + delta

    def _is_update_time(self) -> bool:
        """Return `True` if it's time to run updates."""
        return datetime.datetime.now() >= self._update_time

    def run(self):
        """Run the main loop."""
        try:
            self.reset_update_time()
            while not self._is_update_time():
                time.sleep(self.min_wait_seconds)
            log.info('Updating services')
            self.update_func(self._config)
            # This is used in tests as evidence of completion.
            #   Don't change it without changing the tests
            log.info('Updated services')
        except CertDeployError as err:
            if self._config.fail_fast:
                self._exception = err
            else:
                # Logging here since these don't bubble up to the parent thread
                log.error(err, exc_info=err)
        except Exception as err:
            self._exception = err

    def join(self):
        """Join the thread.

        Also reraise any exception encountered if `fail_fast` is enabled.
        """
        threading.Thread.join(self)
        if self._exception:
            log.debug('Reraising %s', self._exception)
            raise self._exception


class DeployServer:
    """SFTP server to accept certs from the CertDeploy server.

    Arguments:
        config: The CertDeploy client config.
    """

    _stop_running: bool = False

    def __init__(self, config: ClientConfig):  # noqa: D107
        self._config: ClientConfig = config
        self._sftpd_config: SFTPDConfig = self._config.sftpd_config
        self._update: _Update = None
        StubSFTPServer._working_dir: os.PathLike = self._config.source

    def _join_update(self):
        """Join the update worker thread when it's done.

        Raises:
            Any exception encountered by the update worker if `fail_fast` is
            enabled.
        """
        if self._update and not self._update.is_alive():
            # This raises unexpected exceptions from threads
            self._update.join()

    def _deploy(self):
        """Deploy new certificates.

        Raises:
            Any exception encountered by the update worker if `fail_fast` is
            enabled.
        """
        log.info('Deploying new certs')
        if deploy(self._config):
            self._join_update()
            log.info('Queueing updates for services')
            # If there is no update staged or there is an update that has
            #   already been executed, set a new one.
            if not self._update or not self._update.is_alive():
                self._update = _Update(self._config, update_services)
                self._update.start()
            # As long as there were certs deployed reset the delay
            self._update.reset_update_time()

    def serve_forever(self):
        """Start the server and leave it running.

        Raises:
            Any exception encountered by the update worker if `fail_fast` is
                enabled.
            CertDeployError: When unable to listen on the socket.
        """
        log.debug(
            'Opening socket on port %s at address %s',
            self._sftpd_config.listen_port,
            self._sftpd_config.listen_address,
        )
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        server_socket.settimeout(SOCKET_TIMEOUT)
        try:
            server_socket.bind(
                (
                    self._sftpd_config.listen_address,
                    self._sftpd_config.listen_port,
                )
            )
            server_socket.listen(self._sftpd_config.socket_backlog)
        except OSError as err:
            # Provide a more informative error message
            raise CertDeployError(
                'Failed to listen on '
                f'{self._sftpd_config.listen_address or "0.0.0.0"}:'
                f'{self._sftpd_config.listen_port}: {err}'
            ) from err
        # This is used to determine if the client has started running in some
        #   of the tests. Be sure to adjust the tests if you change this.
        log.info(
            'Listening for incoming connections at %s:%s',
            self._sftpd_config.listen_address or '0.0.0.0',
            self._sftpd_config.listen_port,
        )
        while not self._stop_running:
            # socket timeout acts like sleep for this loop
            try:
                conn, addr = server_socket.accept()
            except socket.timeout:
                self._join_update()
                continue
            log.info('Got connection from %s', addr)
            host_key = paramiko.Ed25519Key.from_private_key_file(
                self._sftpd_config.privkey_filename
            )
            transport = paramiko.Transport(conn)
            transport.add_server_key(host_key)
            transport.set_subsystem_handler(
                'sftp',
                paramiko.SFTPServer,
                StubSFTPServer,
            )
            # Catching this exception to make pytest not complain about
            #   unhandled exceptions in threads.
            #   `pytest.PytestUnhandledThreadExceptionWarning`
            try:
                server = SSHServer(self._config)
                transport.start_server(server=server)
                # The channel variable is required for some reason
                channel = transport.accept()  # noqa: F841
                while transport.is_active():
                    time.sleep(1)
            except paramiko.ssh_exception.SSHException as err:
                if self._config.fail_fast:
                    raise err from err
                log.error(err, exc_info=err)
            self._deploy()
        log.debug('Loop finished gracefully')
