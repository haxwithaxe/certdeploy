"""Docker container fixtures and utilities."""

import pathlib
import re
import time
from datetime import datetime
from typing import Any

import _pytest
import pytest
from docker.models.containers import Container
from fixtures.client_config import client_config_file
from fixtures.keys import CLIENT_KEY_NAME, SERVER_KEY_NAME, KeyPair

import docker

CLIENT_DEST_DIR = '/certdeploy/certs'
CLIENT_SOURCE_DIR = '/certdeploy/staging'
CLIENT_CONTAINER_PYTHON_VERSION = '3.10'


class ContainerStatus:
    """Container status strings."""

    CREATED = 'created'
    RESTARTING = 'restarting'
    RUNNING = 'running'
    PAUSED = 'paused'
    EXITED = 'exited'
    DEAD = 'dead'


class ContainerWrapper:
    """A wrapper around `docker.models.containers.Container`.

    `docker.models.containers.Container` attributes are that are not overridden
    are accessible as attributes of instances of this class.
    """

    _wait_timeout_interval: float = 0.1
    """Time to sleep in each run of the wait loop."""

    def __init__(self, client: docker.DockerClient):
        """Create a new `ContainerWrapper`.

        Arguments:
            client (docker.DockerClient): The docker API client.
        """
        self._client = client
        self._container: Container = None

    @property
    def started_at(self) -> datetime:
        """When the container last reached the `running` state."""
        self._container.reload()
        if self._container.status == ContainerStatus.CREATED:
            return None
        started_at = self._container.attrs['State']['StartedAt']
        cleaned = re.sub(r'\.[0-9]+Z', '', started_at)
        return datetime.strptime(cleaned, '%Y-%m-%dT%H:%M:%S')

    def create(self, image: str, **kwargs: Any) -> 'ContainerWrapper':
        """Create a new container.

        Arguments:
            image: The docker image name.

        Keyword Arguments:
            name (str): The container name. If this is given any other
                containers with the same name will be purged before creating
                this new container.
            kwargs: See docs for `docker.client.containers.create`.
        """
        if 'name' in kwargs:
            self._teardown_old(kwargs['name'])
        self._container = self._client.containers.create(image, **kwargs)
        return self

    def has_crashed(self) -> bool:
        """Return `True` if the container probably crashed and stayed down."""
        state = self._container.attrs['State']
        if not state['Running']:
            if state['Errors']:
                return True
            if state['ExitCode'] != 0:
                return True
        return False

    def start(self, wait: bool = True, timeout: int = 60):
        """Start this container.

        Arguments:
            wait: If `True` then this will wait for the container to be
                in the `running` state.
            timeout: The number of seconds to wait before giving up on waiting
                for the container to start. Defaults to 60.

        See docs for `docker.models.containers.Container.start`.
        """
        self._container.start()
        if not wait:
            return
        self.wait_for_status(ContainerStatus.RUNNING, timeout=timeout)
        self._container.reload()

    def teardown(self, timeout: int = 60):
        """Purge the container from the system."""
        # If the container creation errors out there is no container set. To
        #   avoid extra error noise don't try to remove the container if it
        #   isn't set.
        if self._container:
            self._container.remove(force=True)

    def wait_for_status(self, status: ContainerStatus, timeout: int = 60):
        """Wait for the container to be in the specified state.

        Arguments:
            status: The desired status of the container.
            timeout: The number of seconds to wait before giving up on the
                status.
        """
        countdown = int(timeout / self._wait_timeout_interval)
        self._container.reload()
        while self._container.status != status:
            self._container.reload()
            if timeout and countdown < 1:
                raise TimeoutError(
                    f'Waited {timeout} seconds for container '
                    f'{self._container.name} status to be {status} current '
                    f'status is {self._container.status}'
                )
            countdown -= 1
            time.sleep(self._wait_timeout_interval)

    def _teardown_old(self, container_id: str):
        try:
            old = self._client.containers.get(container_id)
        except docker.errors.NotFound:
            return
        old.remove(force=True)

    def __getattr__(self, attr: Any) -> Any:
        """Passthrough any attribute requests.

        Passthrough requests that `self._container` can provide.
        """
        self._container.reload()
        return getattr(self._container, attr)


class ClientContainer(ContainerWrapper):
    """A CertDeploy client docker container wrapper.

    This naively uses the latest `certdeploy-client` locally available.
    """

    etc_path: pathlib.Path = None
    """The host side path to the directory mounted to /etc/certdeploy in the
    container."""
    output_path: pathlib.Path = None
    """The host side path to the directory mounted in the container for the
    client output."""
    config: dict = None
    """The config dict used to create the CertDeploy client config file."""
    keypair: KeyPair = None
    """The key pair created for this client."""
    server_keypair: KeyPair = None
    """The key pair for the associated server. Just for ease of access."""

    @property
    def has_started(self):
        """`True` if the client in the container is ready for connections."""
        started_flag = (b'INFO:certdeploy-client:Listening for incoming '
                        b'connections at ')
        return started_flag in self._container.logs()

    @property
    def is_running(self):
        """`True` if the container is running."""
        return self._container.status == ContainerStatus.RUNNING

    def create(
        self,
        name: str,
        client_config: dict,
        client_keypair: KeyPair,
        server_keypair: KeyPair,
        tmp_path: pathlib.Path,
        do_not_interfere: bool = False,
        with_docker: bool = False,
        volumes: list[str] = None,
        **kwargs: Any
    ) -> 'ClientContainer':
        """Create a container and return an unstarted `ContainerWrapper`.

        Arguments:
            name: Container name.
            client_config (dict): Client config values.
            client_keypair (KeyPair): The key pair for the CertDeploy client.
            server_keypair (KeyPair): The key pair for the CertDeploy server.
            etc_path (pathlib.Path): The path to mount to `/etc/certdeploy` in
                the container.
            mounts (dict, optional): A `dict` of mount target and source pairs.
            with_docker (bool, optional): Add the default docker socket as a
                mount if `True`. Defaults to `False`.
            do_not_interfere (bool, optional): Don't change client configs if
                `True`. Defaults to `False` to set some sensible defaults.

        Keyword Arguments:
            kwargs: Keyword args passed to `docker.client.containers.create`,
                except for the `ports` value which is updated to export the
                CertDeploy client container's listening port.
        """
        client_config = client_config or {}
        volumes = volumes or []
        self.etc_path = tmp_path.joinpath('etc')
        self.etc_path.mkdir()
        self.output_path = tmp_path.joinpath('output')
        self.output_path.mkdir()
        self.keypair = client_keypair
        self.server_keypair = server_keypair
        ## Assemble config dir
        self._prepare_keys()
        self._prepare_config(client_config, do_not_interfere)
        ## Setup docker bits and pieces
        # Add the sftpd listen port to the exported ports so that they can be
        #   accessed from outside of docker
        if self.config.get('sftpd', {}).get('listen_port'):
            port = self.config['sftpd']['listen_port']
            if 'ports' not in kwargs:
                kwargs['ports'] = {}
            kwargs['ports'].update({port: port})
        ## Setup the container
        super().create(
            'certdeploy-client:latest',
            name=name,
            volumes=self._assemble_volumes(volumes, with_docker),
            **kwargs
        )
        return self

    def has_deployed(self, *filenames: str) -> bool:
        """Return `True` if all the files given exists.

        Arguments:
            filenames (list[str]): A list of file names relative to the
                `self.output_path`.

        Returns:
            bool: `True` if all `filenames` are found in `self.output_path`.
        """
        for filename in filenames:
            if not self.output_path(filename).exists():
                return False
        return True

    def has_updated(self) -> bool:
        """Return `True` if the client has finished updating services."""
        if (b'INFO:certdeploy-client:Updated services\n' in
                self._container.logs()):
            return True
        return False

    def start(self, timeout: int = 60):
        """Wait while the client is starting up.

        Arguments:
            timeout: The number of seconds to wait before giving up on the
                client starting. Defaults to 60.
        """
        super().start(wait=False)
        self._container.reload()
        countdown = (timeout or 0)/0.1
        while not self.has_started and not self.has_crashed():
            self._container.reload()
            if timeout and countdown < 1:
                raise TimeoutError(
                    f'Waited {timeout} seconds for the client in container '
                    f'{self._container.name} to start'
                )
            countdown -= 1
            time.sleep(0.1)

    def wait_for_deployed(self, timeout: int = 60):
        """Wait while the client is in progress.

        Arguments:
            timeout: The number of seconds to wait before giving up on the
                status. Defaults to 60.
        """
        self._container.reload()
        countdown = (timeout or 0)/0.1
        while not self.has_updated() and not self.has_crashed():
            self._container.reload()
            if timeout and countdown < 1:
                raise TimeoutError(
                    f'Waited {timeout} seconds for container '
                    f'{self._container.name} to finish running: '
                    f'is_running={self.is_running}, '
                    f'has_crashed={self.has_crashed()}, '
                    f'has_deployed={self.has_deployed()}'
                )
            countdown -= 1
            time.sleep(0.1)

    def _assemble_volumes(self, volumes: list[str], with_docker: bool
                          ) -> list[str]:
        """Combine the volumes given in `volumes` with required volumes.

        Arguments:
            volumes (list[str]): A list of strings describing individual mounts
                like in docker-compose.
            with_docker (bool): Add the docker socket to the list of volumes.

        Returns:
            list[str]: A list of volume specifications.
        """
        real_volumes = [
            f'{self.etc_path}:/etc/certdeploy:ro',
            f'''{self.output_path}:{self.config['destination']}'''
        ]
        if with_docker:
            real_volumes.append('/var/run/docker.sock:/var/run/docker.sock')
        real_volumes.extend(volumes)
        return real_volumes

    def _prepare_config(self, client_config: dict,
                        do_not_interfere: bool):
        """Prepare the config dict to pass to the client config fixture.

        Adds the following to the client config:
            * `destination`
            * `source`
        Adds the following to the `sftpd` section of the client config:
            * `privkey_filename` - Set with the absolute path for inside the
                container.
            * `server_pubkey_filename` - Set with the absolute path for inside
                the container.

        Arguments:
            client_config (dict): The base client config `dict`.
            do_not_interfere (bool): If `True` `client_config` won't be
                changed.
        """
        # If not told to not interfere with configs, then interfere with configs
        if not do_not_interfere:
            # Force source and dest to constant values
            client_config['destination'] = CLIENT_DEST_DIR
            client_config['source'] = CLIENT_SOURCE_DIR
            if 'sftpd' in client_config:
                sftpd = client_config.pop('sftpd')
                sftpd['privkey_filename'] = \
                    f'/etc/certdeploy/{self.keypair.privkey_name}'
                sftpd['server_pubkey_filename'] = \
                    f'/etc/certdeploy/{self.server_keypair.pubkey_name}'
        # Generate a config file and transfer it to the config dir
        context = client_config_file(self.etc_path, client_keypair=self.keypair,
                                     server_keypair=self.server_keypair,
                                     sftpd=sftpd, **client_config)
        self.config = context.config

    def _prepare_keys(self):
        """Prepare server and client key pairs."""
        self.keypair.update(self.etc_path, CLIENT_KEY_NAME,
                            f'{CLIENT_KEY_NAME}.pub')
        self.server_keypair.update(self.etc_path, SERVER_KEY_NAME,
                                   f'{SERVER_KEY_NAME}.pub')
        # Write keys to disk
        self.keypair.pubkey_file()
        self.keypair.privkey_file()
        self.server_keypair.pubkey_file()


def _get_canned_docker_container(started: bool) -> ContainerWrapper:
    """Return a canned container.

    The container is a very minimal container that does nothing. It's suitable
    for testing the client's ability to manage Docker containers.

    Arguments:
        started: If True start the container before returning.
    """
    canned = ContainerWrapper(docker.from_env())
    canned.create(
        'alpine:latest',
        name='certdeploy_test_container',
        entrypoint=['/bin/sh', '-c', 'while true; do sleep 600; done'],
        labels={'certdeploy_test': 'hello'}
    )
    if started:
        canned.start()
    return canned


@pytest.fixture(scope='function')
def canned_docker_container() -> callable:
    """Return a canned `ContainerWrapper` factory.

    The container is a vert minimal container that does nothing. It's suitable
    for testing the client's ability to manage Docker containers.
    """
    containers = []

    def _canned_docker_container(started: bool = True) -> ContainerWrapper:
        """Return a canned `ContainerWrapper`.

        Arguments:
            started: If `True` the container is started on creation.

        Returns:
            ContainerWrapper: A canned container.
        """
        canned = _get_canned_docker_container(started=started)
        containers.append(canned)
        return canned

    yield _canned_docker_container
    for container in containers:
        container.teardown()


@pytest.fixture()
def client_docker_container(tmp_path: pathlib.Path, keypairgen: callable,
                            request: _pytest.fixtures.SubRequest
                            ) -> callable:
    """Return a CertDeploy client docker container factory."""
    clients = []

    def _client_docker_container(
        name: str,
        client_config: dict[str, Any] = None,
        volumes: list[str] = None,
        no_build: bool = False,
        with_docker: bool = False,
        client_keypair: KeyPair = None,
        server_keypair: KeyPair = None,
        do_not_interfere: bool = False,
        **kwargs
    ) -> ClientContainer:
        """Return an unstarted CertDeploy client docker container.

        Arguments:
            name (str):
            client_config (dict[str, Any], optional): The client config as a
                `dict`. Defaults to `{}`.
            volumes (list[str], optional): A list of strings describing
                individual mounts like in docker-compose. `/etc/certdeploy` and
                `/certdeploy/certs` or the configured `destination` will be
                added automatically. The docker socket will be added if
                `with_docker` is `True`. Defaults to `[]`.
            no_build (bool, optional): Mounts the `src/certdeploy` directory in
                this repo in place of the package installed in the container.
                Defaults to `False`.
            with_docker (bool, optional): If `True` adds the local docker
                socket to the volumes to be mounted. Defaults to `False`.
            client_keypair (KeyPair, optional): A key pair for the client.
                Defaults to a freshly generated `KeyPair`.
            server_keypair (KeyPair, optional): A key pair for the server.
                Defaults to a freshly generated `KeyPair`.
            do_not_interfere (bool, optional): If `True` the `client_config`
                will not be modified. Defaults to `False`.

        Keyword Arguments:
            kwargs: Keyword arguments to be passed to
                `docker.client.containers.create`.

        Returns:
            ClientContainer: An unstarted client container wapper configured as
                specified.
        """
        client_config = client_config or {}
        volumes = volumes or []
        client_keypair = client_keypair or keypairgen()
        server_keypair = server_keypair or keypairgen()
        if no_build:
            rootdir = pathlib.Path(request.config.rootdir)
            volumes.append(
                    f'''{rootdir.joinpath('src').joinpath('certdeploy')}:'''
                    f'/usr/local/lib/python{CLIENT_CONTAINER_PYTHON_VERSION}'
                    '/site-packages/certdeploy'
            )
        client = ClientContainer(docker.from_env())
        clients.append(client)
        client.create(
            name=f'certdeploy_test_client_{name}',
            client_config=client_config,
            client_keypair=client_keypair,
            server_keypair=server_keypair,
            tmp_path=tmp_path,
            volumes=volumes,
            with_docker=with_docker,
            **kwargs
        )
        return client

    yield _client_docker_container
    for client in clients:
        client.teardown()
