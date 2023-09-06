
import json
import os
import socket
import time
from datetime import datetime, timedelta
from threading import Semaphore, Thread
from typing import Any, Optional

import paramiko
import schedule
from paramiko.ssh_exception import NoValidConnectionsError, SSHException

from .. import format_error
from ..errors import CertDeployError, ConfigError
from . import log
from .config import ServerConfig
from .config.client import ClientConnection
from .config.server import PushMode
from .renew import renew_certs

ONE_SHOT_TIMEOUT = None  # seconds
GO_FAST_SLEEP = 0.1  # seconds
SLOW_DOWN_SLEEP = 30  # seconds


def _sftp_mkdir(sftp, path, mode=None):
    """Recursively make a remote directory (`path`) if needed."""
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


class _TimeoutTimer:
    """Timeout timer that uses time instead of a counter."""

    def __init__(self, max_runtime: int = None):
        """Prepare the timer.

        Arguments:
            max_runtime: The maximum time to wait in seconds. `None` disables
                the timer. Defaults to `None`.
        """
        self._start = datetime.now()
        self._enabled = False
        if max_runtime is not None and max_runtime > 0:
            self._enabled = True
        self._max_runtime_tdelta = timedelta(seconds=max_runtime or 0)

    def check(self, message=None):
        """Check if the timer has expired.

        Arguments:
            message: A message to pass to the `TimeoutError` if the timer has
                expired.

        Raises:
            TimeoutError: When the timer has expired.
        """
        if not self._enabled:
            return
        if datetime.now() - self._start > self._max_runtime_tdelta:
            raise TimeoutError(message or '')

    @classmethod
    def start(cls, max_runtime: int = None) -> '_TimeoutTimer':
        """Start a new timer.

        Arguments:
            max_runtime: The maximum time to wait in seconds. `None` disables
                the timer. Defaults to `None`.

        Returns:
            A new timer.
        """
        return cls(max_runtime)


class Queue:
    """A queue of push jobs."""

    lock: Semaphore = Semaphore()
    """A lock for writing to the queue file."""

    def __init__(self, server: ServerConfig, mode: str = 'r'):
        """Queue of client hash to lineages to be pushed to clients.

        Arguments:
            server: The config of the parent server.
            mode: The access mode of the queue file. Valid values are 'r'
                read (nonblocking) and 'w' write (blocks writes and reads).
                Defaults to 'r'.
        Note:
            The access locking uses lock files to avoid issues with filesystem
                locks on NFS.
        """
        self._queue: dict = {}
        self._filename: os.PathLike = os.path.join(server.queue_dir,
                                                   'queue.json')
        self._lock_filename = f'{self._filename}.lock'
        if mode not in ('r', 'w'):
            raise ValueError('`mode` must be either "r" or "w".')
        self._mode: str = mode

    @property
    def clients(self) -> list[str]:
        """The client hashes in the queue."""
        return list(self._queue.keys())

    def append(self, client_hash: str, lineage: str):
        """Append a job (`lineage`) to the queue for a given client.

        Arguments:
            client_hash: The value of `ClientConnection.hash` for the client
                that needs the update.
            lineage: The lineage path that needs syncing to the client.
        """
        if client_hash not in self._queue:
            self._queue[client_hash] = []
        self._queue[client_hash].append(lineage)

    def get(self, client_hash: str, default: Any = None) -> list[str]:
        """Get a list of lineages that need to be pushed to a client.

        Arguments:
            client_hash: The value of `ClientConnection.hash` for the client
                being requested.
            default: This will be returned when no client matching `client_hash`
                is found. Defaults to `None`.

        Returns:
            A list of lineages that need to be pushed for the given client.
        """
        client_queue = self._queue.get(client_hash, None)
        if client_queue is None:
            return default
        return (client_queue or []).copy()

    def count(self, client_hash: str) -> int:
        """Return the number of lineages left to push for the given client."""
        client_queue = self._queue.get(client_hash)
        if not client_queue:
            return 0
        return len(client_queue)

    def next(self, client_hash: str) -> str:
        """Return the next lineage to push for the given client."""
        client_queue = self._queue.get(client_hash)
        if not client_queue:
            return None
        lineage = client_queue.pop(0)
        if client_hash in self and not self.get(client_hash):
            del self._queue[client_hash]
        return lineage

    def load(self):
        """Load the queue from the path configured with `queue_dir`.

        This won't load a file that is open for writing.
        """
        if self._mode == 'w':
            raise ValueError('Can\'t use Queue.load() in writable mode.')
        try:
            self._lock()
            self._load()
            return self
        finally:
            self._unlock()

    def _load(self):
        """Load the queue from disk.

        The backend of `self.load`.
        """
        if os.path.exists(self._filename):
            with open(self._filename, 'r') as queue_file:
                try:
                    queue = json.load(queue_file)
                except json.JSONDecodeError as err:
                    raise CertDeployError(
                        'The queue file contains invalid data.'
                    ) from err
                if not isinstance(queue, dict):
                    raise CertDeployError(
                        'The queue file contains invalid data.'
                    )
            self._queue = queue
        else:
            self._queue = {}

    def _dump(self):
        """Write the queue to disk."""
        with open(self._filename, 'w') as queue_file:
            json.dump(self._queue, queue_file)

    def _lock(self):
        """Attempt to lock the queue file for writing."""
        self.lock.acquire()
        while os.path.exists(self._lock_filename):
            time.sleep(0.01)
        open(self._lock_filename, 'w').close()

    def _unlock(self):
        """Release the lock on the queue file."""
        self.lock.release()
        if os.path.exists(self._lock_filename):
            os.remove(self._lock_filename)

    def __contains__(self, key: str):
        """Test if some `key` (`ClientConnection.hash`) exists in the queue."""
        return key in self._queue

    def __enter__(self) -> 'Queue':
        """Attempt to lock and load the queue file."""
        self._lock()
        self._load()
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        """Write the queue file if needed and close it."""
        if self._mode == 'w':
            self._dump()
        self._unlock()

    def __len__(self):
        """Return the length of the queue."""
        return len(self._queue)


class PushWorker(Thread):
    """A worker thread to push lineages to a single client."""

    def __init__(self, server: 'Server', client: ClientConnection,
                 config: ServerConfig):
        """Prepare the worker.

        Arguments:
            server: The `Server` instance creating this worker.
            client: The client connection information.
            config: The CertDeploy server config for the server creating this
                worker.
        """
        Thread.__init__(self, daemon=True)
        self._server = server
        self._client = client
        self._config = config
        self._lineage: str = None
        self._retries: int = self._config.push_retries
        # Prefer the client config over the server config.
        if isinstance(self._client.push_retries, int):
            self._retries = self._client.push_retries
        self._retry_interval: int = self._config.push_retry_interval
        # Prefer the client config over the server config.
        if isinstance(self._client.push_retry_interval, int):
            self._retry_interval = self._client.push_retry_interval
        self._exception: Exception = None
        self._attempt: int = None

    @property
    def client_hash(self) -> str:
        """The hash of the associated client."""
        return self._client.hash

    @property
    def has_error(self) -> bool:
        """Return `True` if there has been an exception in the thread."""
        return self._exception is not None

    def _sync_client(self):
        """Sync the current lineage to the client over SFTP."""
        cert_dir = os.path.join(self._client.path,
                                os.path.basename(self._lineage))
        ssh = paramiko.client.SSHClient()
        if self._client.port == 22:
            hostkey_name = self._client.address
        else:
            hostkey_name = f'[{self._client.address}]:{self._client.port}'
        ssh.get_host_keys().add(hostkey_name, 'ssh-ed25519',
                                self._client.pubkey_blob)
        # Set the safest policy by default
        ssh.set_missing_host_key_policy(paramiko.client.RejectPolicy)
        ssh.connect(hostname=self._client.address, port=self._client.port,
                    username=self._client.username,
                    key_filename=self._config.privkey_filename)
        sftp = ssh.open_sftp()
        # Make the destination directory
        _sftp_mkdir(sftp, cert_dir)
        # Transfer certificates as needed
        if self._client.needs_chain:
            log.debug('Copying %s to %s',
                      os.path.join(self._lineage, 'chain.pem'),
                      os.path.join(cert_dir, 'chain.pem'))
            sftp.put(os.path.join(self._lineage, 'chain.pem'),
                     os.path.join(cert_dir, 'chain.pem'))
        if self._client.needs_fullchain:
            log.debug('Copying %s to %s',
                      os.path.join(self._lineage, 'fullchain.pem'),
                      os.path.join(cert_dir, 'fullchain.pem'))
            sftp.put(os.path.join(self._lineage, 'fullchain.pem'),
                     os.path.join(cert_dir, 'fullchain.pem'))
        if self._client.needs_privkey:
            log.debug('Copying %s to %s',
                      os.path.join(self._lineage, 'privkey.pem'),
                      os.path.join(cert_dir, 'privkey.pem'))
            sftp.put(os.path.join(self._lineage, 'privkey.pem'),
                     os.path.join(cert_dir, 'privkey.pem'))
        sftp.close()

    def _next(self) -> bool:
        """Return `True` if there is another lineage to push.

        This also loads the `self._lineage` variable from the queue.
        """
        with Queue(self._config, 'w') as queue:
            self._lineage = queue.next(self._client.hash)
        return self._lineage is not None

    def run(self):
        """Run the main loop.

        Note:
            This is called automatically by `self.start`.
        """
        while self._next():
            log.info('Pushing %s to %s', self._lineage, self._client)
            for self._attempt in range(self._retries+1):
                log.debug('Attempt #%s of %s retries.', self._attempt,
                          self._retries)
                try:
                    self._sync_client()
                except (CertDeployError, socket.gaierror, SSHException,
                        NoValidConnectionsError) as err:
                    log.error('Error syncing with %s:%s: %s',
                              self._client.address, self._client.port,
                              format_error(err), exc_info=err)
                    if self._config.fail_fast:
                        self._exception = err
                        break  # Go to the next lineage
                    if self._attempt == self._retries:
                        log.warning('Attempt #%s of %s failed. Not retrying '
                                    'sync %s to %s.', self._attempt,
                                    self._retries, self._lineage, self._client)
                        break  # Go to the next lineage
                    log.info('Attempt #%s failed. Retrying sync to %s in '
                             '%s seconds.', self._attempt, self._client,
                             self._retry_interval)
                    # Wait between attempts
                    time.sleep(self._retry_interval)
                except Exception as err:
                    self._exception = err
                    if not self._config.fail_fast:
                        log.error('Error syncing with %s:%s: %s',
                                  self._client.address, self._client.port,
                                  format_error(err), exc_info=err)
                    return  # End the thread
                else:
                    log.info('Pushed %s to %s in %s attempts',
                             self._lineage, self._client, self._attempt)
                    break  # Go to the next lineage

    def join(self, timeout: Optional[float] = None):
        """Join the worker thread and raise an exception.

        Arguments:
            timeout: The number of seconds to wait for the thread to end before
                raising a `TimeoutError`. Defaults to `None`.

        Raises:
            An exception if one was encountered and `fail_fast` is enabled.
        """
        Thread.join(self, timeout)
        if self._config.fail_fast and self._exception:
            raise self._exception

    def __repr__(self):
        """Return a pragmatic representation of this object."""
        return (f'<{self.__class__.__name__} address={self._client.address}, '
                f'port={self._client.port}, username={self._client.username},'
                f'attempts={self._attempt}, exception={self._exception}>')


class Server:
    """Accept new sync requests and push new certs to clients."""

    def __init__(self, config: ServerConfig):
        """Prepare the server.

        Arguments:
            config: Server config.
        """
        self._config = config
        self._workers: dict[str, PushWorker] = {}
        self._schedule_renew()

    def serve_forever(self, one_shot: bool = False):
        """Push queued lineages to clients.

        Arguments:
            one_shot: Push lineages in the queue and exit when the queue has
                been fully processed. Defaults to `False`.
        """
        # This is used in tests to determine if the server has started.
        log.debug('Server.serve_forever: one_shot=%s', one_shot)
        # `timeout` is just for debugging. It makes the whole server fail hard
        #   if it takes too long. In order to use it set `ONE_SHOT_TIMEOUT`
        #   to a positive integer.
        timeout = _TimeoutTimer.start(ONE_SHOT_TIMEOUT)
        while True:
            main_loop_sleep = GO_FAST_SLEEP
            queue = Queue(self._config, 'r').load()
            log.debug('Queue length is %s, worker count is %s', len(queue),
                      len(self._workers))
            if len(queue) < 1 and len(self._workers) < 1:
                # Slow down when the queue is empty and there are no workers.
                main_loop_sleep = SLOW_DOWN_SLEEP
                if one_shot:
                    # Once the queue is empty and there are no more workers,
                    #   all the jobs sent with the push only option have
                    #   completed and this loop doesn't need to run anymore.
                    return
            for client in self._config.clients:
                if client.hash not in queue:
                    continue
                if client.hash not in self._workers:
                    self._add_worker(client)
                    if self._config.push_mode == PushMode.SERIAL:
                        log.debug('Waiting for push to %s to finish',
                                  client)
                        self._workers[client.hash].join(
                            self._config.join_timeout
                        )
                    # Only delay when adding a new worker
                    time.sleep(self._config.push_interval)
            # Cleanup workers if idle
            for worker in list(self._workers.values()):
                if not worker.is_alive():
                    self._remove_worker(worker)
            schedule.run_pending()  # Renew certs if needed
            # This is just for debugging. It makes the whole server fail hard
            #   if it takes too long. In order to use it set `ONE_SHOT_TIMEOUT`
            #   to a positive integer.
            if one_shot:
                timeout.check()
            # End just for debugging
            time.sleep(main_loop_sleep)

    def sync(self, lineage: os.PathLike, domains: list[str]):
        """Synchronize clients that need updates based on domains.

        Arguments:
            lineage: The full path of a lineage.
            domains: A `list` of domain names to use to find clients to push
                to.
        """
        for client in self._config.clients:
            for domain in domains:
                if domain in client.domains:
                    with Queue(self._config, 'w') as queue:
                        queue.append(client.hash,  lineage)
                        log.debug('Queued lineage %s for client %s', lineage,
                                  client)
                    break

    def _add_worker(self, client: ClientConnection):
        """Kickstart a new `PushWorker` for `client`."""
        worker = PushWorker(self, client, self._config)
        self._workers[client.hash] = worker
        worker.start()

    def _remove_worker(self, worker):
        """End `worker` and pop it out of the pool."""
        worker.join(self._config.join_timeout)
        del self._workers[worker.client_hash]

    def _schedule_renew(self):
        """Attempt to configure a scheduled cert renewal.

        Raises:
            ConfigError: When renew related configs are invalid.
        """
        # Catch config related errors and add some context before reraising.
        try:
            every = schedule.every(self._config.renew_every)
        except schedule.ScheduleValueError as err:
            raise ConfigError(f'Invalid `renew_every` value: {err}') from err
        try:
            when = getattr(every, self._config.renew_unit)
        except schedule.ScheduleValueError as err:
            raise ConfigError(f'Invalid `renew_unit` value: {err}') from err
        if self._config.renew_at:
            try:
                when = when.at(self._config.renew_at)
            except schedule.ScheduleValueError as err:
                raise ConfigError(f'Invalid `renew_at` value: {err}') from err
        when.do(renew_certs, config=self._config)
