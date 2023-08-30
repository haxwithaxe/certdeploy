"""Docker container fixtures and utilities."""

import enum
import re
import time
from datetime import datetime
from typing import Any

import pytest
from docker.models.containers import Container

import docker


class ContainerStatus(enum.Enum):
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

    Arguments:
        client: The docker API client.
    """

    _wait_timeout_interval = 0.1

    def __init__(self, client: docker.APIClient):
        self._client = client
        self._container: Container = None

    def create(self, image: str, **kwargs: Any):
        """Create a new container.

        Arguments:
            image: The docker image name.

        Keyword Arguments:
            name (str): The container name. If this is given any other
                containers with the same name will be purged before creating
                this new container.
            kwargs: See docs for `docker.containers.create`.
        """
        if 'name' in kwargs:
            self._teardown_old(kwargs['name'])
        self._container = self._client.containers.create(image, **kwargs)
        return self

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

    def wait_for_status(self, status: ContainerStatus, timeout: int = 60):
        """Wait for the container to be in the specified state.

        Arguments:
            status: The desired status of the container.
            timeout: The number of seconds to wait before giving up on the
                status.
        """
        status = status.value if isinstance(status, ContainerStatus) else status
        countdown = int(timeout / self._wait_timeout_interval)
        self._container.reload()
        while self._container.status != status:
            self._container.reload()
            if not countdown % 10:
                print(self._container.name, 'waiting for', status, 'have',
                      self._container.status,
                      int(countdown*self._wait_timeout_interval),
                      countdown,
                      timeout)
            if timeout and countdown < 1:
                raise TimeoutError(
                    f'Waited {timeout} seconds for container '
                    f'{self._container.name} status to be {status} current '
                    f'status is {self._container.status}'
                )
            countdown -= 1
            time.sleep(self._wait_timeout_interval)

    @property
    def started_at(self) -> datetime:
        """When the container last reached the `running` state."""
        self._container.reload()
        if self._container.status == ContainerStatus.CREATED.value:
            return None
        started_at = self._container.attrs['State']['StartedAt']
        cleaned = re.sub(r'\.[0-9]+Z', '', started_at)
        return datetime.strptime(cleaned, '%Y-%m-%dT%H:%M:%S')

    def teardown(self, timeout: int = 60):
        """Purge the container from the system."""
        self._container.remove(force=True)

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
        if hasattr(self._container, attr):
            return getattr(self._container, attr)
        raise AttributeError(attr)


def _canned_docker_container(started: bool) -> ContainerWrapper:
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

    def _canned_container(started: bool = True) -> ContainerWrapper:
        """Return a canned `ContainerWrapper`.

        Arguments:
            started: If `True` the container is started on creation.

        Returns:
            ContainerWrapper: A canned container.
        """
        canned = _canned_docker_container(started=started)
        containers.append(canned)
        return canned

    yield _canned_container
    for container in containers:
        container.teardown()
