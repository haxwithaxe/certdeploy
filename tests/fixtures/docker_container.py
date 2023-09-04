"""Docker container fixtures and utilities."""

import pathlib
import re
import time
from datetime import datetime
from typing import Any, Callable

import _pytest
import pytest
from docker.models.containers import Container
from fixtures.client_config import client_config_file
from fixtures.keys import CLIENT_KEY_NAME, SERVER_KEY_NAME, KeyPair
from fixtures.server_config import server_config_file

import docker

CLIENT_CONTAINER_PYTHON_VERSION = '3.10'


class ContainerStatus:
    """Container status strings."""

    CREATED: str = 'created'
    RESTARTING: str = 'restarting'
    RUNNING: str = 'running'
    PAUSED: str = 'paused'
    EXITED: str = 'exited'
    DEAD: str = 'dead'


class ContainerCrashed(Exception):
    """Indicates that a container has crashed while waiting for it."""


class ContainerWrapper:
    """A wrapper around `docker.models.containers.Container`.

    `docker.models.containers.Container` attributes are that are not overridden
    are accessible as attributes of instances of this class.
    """

    # If this is set to something above 1 the wait_for_condition method needs
    #   updating.
    _wait_timeout_interval: float = 0.1
    """Time to sleep in each run of any of the wait loops."""

    def __init__(self, client: docker.DockerClient):
        """Create a new `ContainerWrapper`.

        Arguments:
            client: The docker API client.
        """
        self._client = client
        self._container: Container = None

    @property
    def has_crashed(self) -> bool:
        """Return `True` if the container probably crashed and stayed down."""
        state = self._container.attrs['State']
        if not state['Running']:
            if state['Error']:
                return True
            if state['ExitCode'] != 0:
                return True
            if state['OOMKilled']:
                return True
        return False

    @property
    def ipv4_address(self) -> str:
        """The primary IPv4 address of the container."""
        return self._container.attrs['NetworkSettings']['IPAddress']

    @property
    def is_running(self) -> bool:
        """`True` if the container is running."""
        return self._container.status == ContainerStatus.RUNNING

    @property
    def started_at(self) -> datetime:
        """When the container last reached the `running` status."""
        self._container.reload()
        # If the container state is still `created` don't bother continuing.
        if self._container.status == ContainerStatus.CREATED:
            return None
        started_at = self._container.attrs['State']['StartedAt']
        # Transform the time into a format datetime can handle.
        cleaned = re.sub(r'\.[0-9]+Z', '', started_at)
        return datetime.strptime(cleaned, '%Y-%m-%dT%H:%M:%S')

    def create(self, image: str, name: str = None, **kwargs: Any
               ) -> 'ContainerWrapper':
        """Create a new container.

        Arguments:
            image: The docker image name.
            name: The container name. If this is given any other containers
                with the same name will be purged before creating this new
                container.

        Keyword Arguments:
            kwargs: See docs for `docker.client.containers.create`.
        """
        if name:
            self._teardown_old(name)
            kwargs['name'] = name
        self._container = self._client.containers.create(image, **kwargs)
        return self

    def start(self, wait: bool = True, timeout: int = 60):
        """Start this container.

        Arguments:
            wait: If `True` then this will wait for the container to be
                in the `running` state. Defaults to `True`.
            timeout: The number of seconds to wait before giving up on waiting
                for the container to start. Defaults to 60.

        See docs for `docker.models.containers.Container.start`.
        """
        self._container.start()
        if not wait:
            return
        self.wait_for_status(ContainerStatus.RUNNING, timeout=timeout)

    def teardown(self):
        """Purge the container from the system."""
        # If the container creation errors out there is no container set. To
        #   avoid extra error noise don't try to remove the container if it
        #   isn't set.
        if self._container:
            self._container.remove(force=True)

    def wait_for_condition(self,
                           condition: Callable[['ContainerWrapper'], bool],
                           timeout: int = 60):
        """Wait for some `condition` to occur in the container.

        Arguments:
            condition: A `callable` that takes this `ContainerWrapper` as the
                only argument.
            timeout: The number of seconds to wait before giving up on the
                `condition`. Defaults to 60.

        Raises:
            ContainerCrashed: If the container state indicates it has crashed.
        """
        # This assumes that `self._wait_timeout_interval` is less than 1
        countdown = int(timeout / self._wait_timeout_interval)
        self._container.reload()
        while not condition(self):
            self._container.reload()
            if timeout and countdown < 1:
                raise TimeoutError(
                    f'Waited {timeout} seconds for container '
                    f'{self._container.name} to meet the condition {condition}'
                )
            if self.has_crashed:
                raise ContainerCrashed(
                    f'{self.name}:\n{self._container.logs().decode()}'
                )
            countdown -= 1
            time.sleep(self._wait_timeout_interval)

    def wait_for_log(self, match_bytes: bytes, timeout: int = 60):
        """Wait for `match_bytes` to occur in the container logs.

        Arguments:
            match_bytes: The byte string to look for in the logs.
            timeout: The number of seconds to wait before giving up on the
                match. Defaults to 60.
        """
        self.wait_for_condition((lambda x: match_bytes in x.logs()), timeout)

    def wait_for_status(self, status: ContainerStatus, timeout: int = 60):
        """Wait for the container to be in the specified state.

        Arguments:
            status: The desired status of the container.
            timeout: The number of seconds to wait before giving up on the
                status. Defaults to 60.
        """
        self.wait_for_condition((lambda x: x.status == status), timeout)

    def _teardown_old(self, container_id: str):
        """Tear down any existing containers with the same name.

        Arguments:
            container_id: This can be the id hash or the container name.
        """
        try:
            old = self._client.containers.get(container_id)
        except docker.errors.NotFound:
            return
        old.remove(force=True)

    def __getattr__(self, attr: Any) -> Any:
        """Passthrough any attribute requests.

        Passthrough requests that `docker.models.containers.Container` can
        provide.
        """
        if self._container:
            self._container.reload()
        return getattr(self._container, attr)


class ContainerInternalPaths:
    """The paths inside the container that will be mounted to.

    The idea is that these will be inspectable during the tests.
    """

    etc: pathlib.Path = pathlib.Path('/etc/certdeploy')
    """The config directory."""
    output: pathlib.Path = pathlib.Path('/certdeploy/')
    """The output directory. In clients this is where the source and destination
    directories are made. In servers this is where the queue directory is made.
    """
    # This is created in the server Dockerfile
    queue: pathlib.Path = pathlib.Path('/var/run/certdeploy')
    """The server's queue directory."""
    # This is created in the client Dockerfile
    dest: pathlib.Path = output.joinpath('certs')
    """The client's certificate output directory."""
    # This is created in the client Dockerfile
    source: pathlib.Path = output.joinpath('staging')
    """The client's certificate staging directory."""


class CertDeployContainerWrapper(ContainerWrapper):
    """Base CertDeploy container wrapper."""

    container_paths = ContainerInternalPaths
    """Paths for inside the container."""
    etc_path: pathlib.Path = None
    """The host side path to the directory mounted to `self.container_paths.etc`
    in the container."""
    output_path: pathlib.Path = None
    """The host side path to the directory mounted in the container for the
    output."""
    config: dict = None
    """The config dict used to create the config file."""
    client_keypair: KeyPair = None
    """The key pair created for the client."""
    server_keypair: KeyPair = None
    """The key pair created for the server."""
    image: str = None
    """Docker image name."""
    type_name: str = 'generic'
    """Internal use only. Used in log messages and errors."""
    has_started_flag: bytes = (b'INFO:certdeploy-client:Listening for incoming '
                               b'connections at ')
    """The encoded string that signals the client or server is ready to use."""

    @property
    def has_started(self):
        """`True` if the component in the container is ready to use."""
        return self.has_started_flag in self._container.logs()

    def create(
        self,
        name: str,
        config: dict,
        client_keypair: KeyPair,
        server_keypair: KeyPair,
        tmp_path: pathlib.Path,
        do_not_interfere: bool = False,
        with_docker: bool = False,
        volumes: list[str] = None,
        **kwargs: Any
    ) -> 'CertDeployContainerWrapper':
        """Create a container and return an unstarted container.

        Arguments:
            name: Container name.
            config: Config values.
            client_keypair: The key pair for the CertDeploy client.
            server_keypair: The key pair for the CertDeploy server.
            etc_path: The path to mount to `self.container_paths.etc` in the
                container.
            with_docker: Add the default docker socket as a volume if `True`.
                Defaults to `False`.
            volumes: A list of volume declarations just like in a docker-compose
                file. Defaults to an empty `list`.
            do_not_interfere: If `True` `config` will not be altered before
                being converted into a config file. Defaults to `False` to set
                some sensible defaults.

        Keyword Arguments:
            kwargs: Keyword args passed to `docker.client.containers.create`,
                except for the `ports` value which is updated to export the
                CertDeploy client container's listening port.
        Returns:
            An instance of this kind of container wrapper.
        """
        config = config or {}
        volumes = volumes or []
        self.etc_path = tmp_path.joinpath('etc')
        self.etc_path.mkdir()
        self.output_path = tmp_path.joinpath('output')
        self.output_path.mkdir()
        self.client_keypair = client_keypair
        self.server_keypair = server_keypair
        # Assemble config dir
        self.prepare_keys()
        self.prepare_config(config, do_not_interfere)
        # Preprocess kwargs for create
        self.precreate(kwargs)
        # Setup the container
        super().create(
            image=self.image,
            name=name,
            volumes=self._assemble_volumes(volumes, with_docker),
            **kwargs
        )
        return self

    def precreate(self, create_kwargs: dict):
        """Do things that need to happen before calling `super().create`.

        Do things that need to happen after the config is ready and before
        `super().create` is called.

        Arguments:
            create_kwargs: The keyword arguments to be passed to
                `docker.client.containers.create`.
        """
        pass

    def prepare_config(self, config: dict, do_not_interfere: bool):
        """Prepare the config.

        Must populate `self.config`.

        Arguments:
            config: The config `dict` for the client/server.
            do_not_interfere: If `True` `config` will not be interfered with
                by this method.
        """
        raise NotImplementedError()

    def prepare_keys(self):
        """Prepare server and client key pairs."""
        # Populate the key pairs with the info from this object, but don't
        #   overwrite the path or privkey name of the keys.
        if (not self.client_keypair.path or
                not self.client_keypair.privkey_name):
            self.client_keypair.update(self.etc_path, CLIENT_KEY_NAME,
                                       f'{CLIENT_KEY_NAME}.pub')
        if (not self.server_keypair.path or
                not self.server_keypair.privkey_name):
            self.server_keypair.update(self.etc_path, SERVER_KEY_NAME,
                                       f'{SERVER_KEY_NAME}.pub')
        # Write keys to disk
        self.client_keypair.pubkey_file()
        self.client_keypair.privkey_file()
        self.server_keypair.pubkey_file()
        self.server_keypair.privkey_file()

    def start(self, timeout: int = 60):
        """Start the container and wait for the client/server to be ready.

        Arguments:
            timeout: The number of seconds to wait before giving up on the
                component starting. If timeout is falsey this will not wait for
                the container to start or be ready. Defaults to 60.
        """
        super().start(wait=False)
        if not timeout:
            return
        self._container.reload()

        def _condition(container):
            return (container.status == ContainerStatus.RUNNING and
                    container.has_started)

        self.wait_for_condition(_condition)

    def _assemble_volumes(self, volumes: list[str], with_docker: bool
                          ) -> list[str]:
        """Combine the volumes given in `volumes` with required volumes.

        Arguments:
            volumes: A list of strings describing individual mounts
                like in docker-compose.
            with_docker: Add the docker socket to the list of volumes.

        Returns:
            A list of volume specifications.
        """
        real_volumes = [
            f'{self.etc_path}:/etc/certdeploy:ro',
        ]
        if 'destination' in self.config:
            real_volumes.append(
                f'''{self.output_path}:{self.config['destination']}'''
            )
        if 'queue_dir' in self.config:
            real_volumes.append(
                f'''{self.output_path}:{self.config['queue_dir']}'''
            )
        if with_docker:
            real_volumes.append('/var/run/docker.sock:/var/run/docker.sock')
        real_volumes.extend(volumes)
        return real_volumes


class ClientContainer(CertDeployContainerWrapper):
    """A CertDeploy client docker container wrapper.

    This naively uses the latest `certdeploy-client` locally available.
    """

    has_started_flag: bytes = (b'INFO:certdeploy-client:Listening for '
                               b'incoming connections at ')
    image: str = 'certdeploy-client:latest'
    """Docker image name."""
    type_name: str = 'client'
    """Internal use only. Used in log messages and errors."""

    @property
    def has_updated(self) -> bool:
        """`True` if the client has finished updating services."""
        if (b'INFO:certdeploy-client:Updated services\n' in
                self._container.logs()):
            return True
        return False

    def has_deployed(self, *filenames: str) -> bool:
        """Return `True` if all the files given exists.

        Arguments:
            filenames: A list of file names relative to the
                `self.output_path`.

        Returns:
            `True` if all `filenames` are found in `self.output_path`.
        """
        for filename in filenames:
            if not self.output_path(filename).exists():
                return False
        return True

    def precreate(self, create_kwargs: dict):
        """Prepare the keyword arguments for `docker.client.containers.create`.

        Arguments:
            create_kwargs: The keyword arguments to be passed to
                `docker.client.containers.create`.
        """
        # Add the sftpd listen port to the exported ports so that they can be
        #   accessed from outside of docker
        if self.config.get('sftpd', {}).get('listen_port'):
            port = self.config['sftpd']['listen_port']
            if 'ports' not in create_kwargs:
                create_kwargs['ports'] = {}
            create_kwargs['ports'].update({port: port})

    def prepare_config(self, config: dict,
                       do_not_interfere: bool):
        """Prepare the config dict to pass to the client config fixture.

        Populates `self.config`.

        Adds the following to the client config:
            * `destination`
            * `source`
        Adds the following to the `sftpd` section of the client config:
            * `privkey_filename` - Set with the absolute path for inside the
                container.
            * `server_pubkey_filename` - Set with the absolute path for inside
                the container.

        Arguments:
            config: The base client config `dict`.
            do_not_interfere: If `True` `config` won't be changed.
        """
        if not do_not_interfere:
            # Force source and dest to constant values
            config['destination'] = str(self.container_paths.dest)
            config['source'] = str(self.container_paths.source)
            sftpd = {}
            if 'sftpd' in config:
                sftpd = config.pop('sftpd')
            sftpd['privkey_filename'] = str(self.container_paths.etc.joinpath(
                self.client_keypair.privkey_name
            ))
            sftpd['server_pubkey_filename'] = str(
                self.container_paths.etc.joinpath(
                    self.server_keypair.pubkey_name
                )
            )
        # Generate a config file and transfer it to the config dir
        context = client_config_file(
            self.etc_path,
            client_keypair=self.client_keypair,
            server_keypair=self.server_keypair,
            sftpd=sftpd,
            **config
        )
        self.config = context.config

    def wait_for_updated(self, timeout: int = 60):
        """Wait for the client to finish updating services.

        Arguments:
            timeout: The number of seconds to wait before giving up on the
                status. If `timeout` is falsey then this will not wait.
                Defaults to 60.
        """
        self.wait_for_condition((lambda x: x.has_updated), timeout)


class ServerContainer(CertDeployContainerWrapper):
    """A CertDeploy server docker container wrapper.

    This naively uses the latest `certdeploy-server` available on the host.
    """

    has_started_flag: bytes = (b'DEBUG:certdeploy-server: '
                               b'Server.serve_forever: one_shot=')
    """The string in the logs that indicates the server is ready."""
    image: str = 'certdeploy-server:latest'
    """Docker image name."""
    type_name: str = 'server'
    """Internal use only. Used in log messages and errors."""

    def prepare_config(self, config: dict, do_not_interfere: bool):
        """Prepare `config` to pass to the server config fixture.

        Populates `self.config`.

        Adds the following to the server configs:
            * `queue_dir`
            * `privkey_filename`
            * The same `pubkey` for all `client_configs`

        Arguments:
            config: The base server config `dict`.
            do_not_interfere: If `True` `config` won't be changed.
        """
        if not do_not_interfere:
            # Force queue_dir value
            config['queue_dir'] = str(self.container_paths.queue)
            # Force privkey_filename value
            config['privkey_filename'] = str(self.container_paths.etc.joinpath(
                self.server_keypair.privkey_file().name
            ))
            # Force the pubkey values for all client connections
            for client_conn in config.get('client_configs', []):
                client_conn['pubkey'] = self.client_keypair.pubkey_text
        # Generate a config file and transfer it to the config dir
        context = server_config_file(
            self.etc_path,
            client_keypair=self.client_keypair,
            server_keypair=self.server_keypair,
            **config
        )
        self.config = context.config


def _get_canned_docker_container(started: bool) -> ContainerWrapper:
    """Return a canned container.

    The container is a very minimal container that does nothing. It's suitable
    for testing the client's ability to manage Docker containers.

    Arguments:
        started: If `True` start the container before returning.
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
def canned_docker_container() -> Callable[[bool], ContainerWrapper]:
    """Return a canned `ContainerWrapper` factory.

    The container is a vert minimal container that does nothing. It's suitable
    for testing the client's ability to manage Docker containers.
    """
    containers = []

    def _canned_docker_container(started: bool = True) -> ContainerWrapper:
        """Return a canned `ContainerWrapper`.

        Arguments:
            started: If `True` the container is started on creation. Defaults
                to `True`.

        Returns:
            A canned container.
        """
        canned = _get_canned_docker_container(started=started)
        containers.append(canned)
        return canned

    yield _canned_docker_container
    for container in containers:
        container.teardown()


@pytest.fixture()
def client_docker_container(
    tmp_path: pathlib.Path,
    keypairgen: Callable[[], KeyPair],
    request: _pytest.fixtures.SubRequest
) -> Callable[
    [str, dict[str, Any], list[str], bool, bool, KeyPair, KeyPair, bool, ...],
    ClientContainer
]:
    """Return a CertDeploy client docker container factory."""
    clients = []

    def _client_docker_container(
        name: str,
        config: dict[str, Any] = None,
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
            name: Container name suffix. The prefix is
                `certdeploy_test_client_`.
            config: The client config as a `dict`. Defaults to `{}`.
            volumes: A list of strings describing individual mounts like in
                docker-compose. `ContainerInternalPaths.etc` and
                `ContainerInternalPaths.dest` or the configured `destination`
                will be added automatically. The docker socket will be added if
                `with_docker` is `True`. Defaults to `[]`.
            no_build: Mounts the `src/certdeploy` directory in this repo in
                place of the package installed in the container. This relies on
                the python version in `CLIENT_CONTAINER_PYTHON_VERSION` matching
                the client container's python version. Defaults to `False`.
            with_docker: If `True` adds the local docker socket to the volumes
                to be mounted. Defaults to `False`.
            client_keypair: A key pair for the client. Defaults to a freshly
                generated `KeyPair`.
            server_keypair: A key pair for the server. Defaults to a freshly
                generated `KeyPair`.
            do_not_interfere: If `True` the `config` will not be modified.
                Defaults to `False`.

        Keyword Arguments:
            kwargs: Keyword arguments to be passed to
                `docker.client.containers.create`.

        Returns:
            An unstarted client container wrapper configured as specified.
        """
        config = config or {}
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
            config=config,
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


@pytest.fixture()
def server_docker_container(
    tmp_path: pathlib.Path,
    keypairgen: Callable[[], KeyPair],
    request: _pytest.fixtures.SubRequest
) -> Callable[
    [str, dict[str, Any], list[str], bool, bool, KeyPair, KeyPair, bool, ...],
    ServerContainer
]:
    """Return a CertDeploy server docker container factory."""
    servers = []

    def _server_docker_container(
        name: str,
        config: dict[str, Any] = None,
        volumes: list[str] = None,
        no_build: bool = False,
        with_docker: bool = False,
        client_keypair: KeyPair = None,
        server_keypair: KeyPair = None,
        do_not_interfere: bool = False,
        **kwargs
    ) -> ServerContainer:
        """Return an unstarted CertDeploy server docker container.

        Arguments:
            name: The service name suffix. The prefix is
                `certdeploy_test_server_`.
            config: The client config as a `dict`. Defaults to `{}`.
            volumes: A list of strings describing individual mounts like in
                docker-compose. `/etc/certdeploy` and the configured `queue_dir`
                will be added automatically. The docker socket will be added if
                `with_docker` is `True`. Defaults to `[]`.
            no_build: Mounts the `src/certdeploy` directory in this repo in
                place of the package installed in the container. This relies on
                the python version in `CLIENT_CONTAINER_PYTHON_VERSION` matching
                the client container's python version. Defaults to `False`.
            with_docker: If `True` adds the local docker socket to the volumes
                to be mounted. Defaults to `False`.
            client_keypair: A key pair for the client. Defaults to a freshly
                generated `KeyPair`.
            server_keypair: A key pair for the server. Defaults to a freshly
                generated `KeyPair`.
            do_not_interfere: If `True` the `config` will not be
                modified. Defaults to `False`.

        Keyword Arguments:
            kwargs: Keyword arguments to be passed to
                `docker.client.containers.create`.

        Returns:
            An unstarted server container wrapper configured as specified.
        """
        config = config or {}
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
        server = ServerContainer(docker.from_env())
        servers.append(server)
        server.create(
            name=f'certdeploy_test_server_{name}',
            config=config,
            client_keypair=client_keypair,
            server_keypair=server_keypair,
            tmp_path=tmp_path,
            volumes=volumes,
            with_docker=with_docker,
            **kwargs
        )
        return server

    yield _server_docker_container
    for server in servers:
        server.teardown()
