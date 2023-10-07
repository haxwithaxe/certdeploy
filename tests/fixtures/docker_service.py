"""Docker service fixtures and utilities."""

import re
import time
from datetime import datetime
from typing import Any, Callable, Generator

import pytest
from docker.models.services import Service

import docker


class ServiceCrashed(Exception):
    """Indicates a service has crashed."""


LIVE_TASK_STATES = [
    'new',
    'pending',
    'assigned',
    'accepted',
    'ready',
    'preparing',
    'starting',
    'running',
]
DEAD_TASK_STATES = [
    'complete',
    'failed',
    'shutdown',
    'rejected',
    'orphaned',
    'remove',
]


def _timestamp_to_datetime(timestamp: str) -> datetime:
    cleaned = re.sub(r'\.[0-9]+Z', '', timestamp)
    return datetime.strptime(cleaned, '%Y-%m-%dT%H:%M:%S')


class ServiceWrapper:
    """A wrapper around `docker.models.services.Service`.

    `docker.models.services.Service` attributes are that are not overridden
    are accessible as attributes of instances of this class.
    """

    _wait_timeout_interval = 0.1

    def __init__(self, client: docker.DockerClient):
        """Prepare service wrapper.

        Arguments:
            client: The docker API client.
        """
        self._client = client
        self._service: Service = None

    @property
    def created_at(self) -> datetime:
        """When the service was created."""
        self._service.reload()
        return _timestamp_to_datetime(self._service.attrs['CreatedAt'])

    @property
    def has_crashed(self):
        """`True` if the service has any failed tasks.

        In this case failed means *any* task that either has the `failed` state
        or a non-zero exit code.
        """

        def _filter(task: dict) -> bool:
            status = task['Status'].get('ContainerStatus', {})
            exit_code = status.get('ExitCode')
            if exit_code is None:
                return False
            return exit_code != 0 or task['Status']['State'] == 'failed'

        for task in self.filter_tasks(_filter):
            return True
        return False

    @property
    def is_ready(self):
        """`True` if the service is started and running."""
        self._service.reload()
        mode = self._service.attrs['Spec']['Mode']
        replicas = mode.get('Replicated', {}).get('Replicas')
        if replicas is None:
            return False
        active_tasks_gen = self.filter_tasks(
            lambda x: x['Status']['State'] == 'running'
        )
        return len([t for t in active_tasks_gen]) == replicas

    @property
    def is_stopped(self):
        """`True` if the service is stopped."""
        active_tasks = self.filter_tasks(
            lambda x: x['Status']['State'] in LIVE_TASK_STATES
        )
        for _ in active_tasks:
            return False
        return True

    @property
    def live_tasks(self) -> Generator[dict, None, None]:
        """Tasks in some form of live state."""

        def is_alive(task):
            return task['Status']['State'] in LIVE_TASK_STATES

        yield from self.filter_tasks(is_alive)

    @property
    def updated_at(self) -> datetime:
        """When the service was last updated."""
        self._service.reload()
        return _timestamp_to_datetime(self._service.attrs['UpdatedAt'])

    def create(self, image: str, timeout: int = 60, **kwargs: Any):
        """Create a new service.

        Arguments:
            image: The docker image name.
            timeout: The number of seconds to wait for the service to be ready.
                If `None` this will return as soon as the service has been
                created. Defaults to 60.

        Keyword Arguments:
            name (str): The service name. If this is given any other
                services with the same name will be purged before creating
                this new service.
            kwargs: See docs for `docker.client.services.create`.
        """
        if 'name' in kwargs:
            self._teardown_old(kwargs['name'])
        self._service = self._client.services.create(image, **kwargs)
        if timeout:
            self.wait_for_condition(lambda x: x.is_ready, timeout=timeout)
        return self

    def filter_tasks(
        self, task_filter: Callable[[dict], bool]
    ) -> Generator[dict, None, None]:
        """Filter service tasks with `task_filter`.

        Arguments:
            task_filter: A `callable` that accepts a task `dict` and returns
                `True` if the task matches.

        Yields:
            Task `dict`s as they are identified.
        """
        self._service.reload()
        for task in self._service.tasks():
            if task_filter(task):
                yield task

    def teardown(self, timeout: int = 60):
        """Purge the service from the system.

        Arguments:
            timeout: The number of seconds to wait before giving up on removing
                the service.

        Raises:
            TimeoutError: When `timeout` seconds have passed without the
                service being removed.
            ServiceCrashed: When the service looks like it's crashed.
        """
        self._service.remove()
        if not timeout:
            return
        try:
            self.wait_for_condition(lambda x: x.is_stopped, timeout=timeout)
        except docker.errors.NotFound:
            pass

    def wait_for_condition(
        self, condition: Callable[['ServiceWrapper'], bool], timeout: int = 60
    ):
        """Wait for some `condition` to occur in the service.

        Arguments:
            condition: A `callable` that takes this `ServiceWrapper` as the
                only argument.
            timeout: The number of seconds to wait before giving up on the
                `condition`. Defaults to 60.

        Raises:
            ServiceCrashed: If the service state indicates it has crashed.
        """
        # This assumes that `self._wait_timeout_interval` is less than 1
        countdown = int(timeout / self._wait_timeout_interval)
        self._service.reload()
        while not condition(self):
            self._service.reload()
            if timeout and countdown < 1:
                raise TimeoutError(
                    f'Waited {timeout} seconds for service '
                    f'{self._service.name} to meet the condition {condition}'
                )
            if self.has_crashed:
                raise ServiceCrashed(
                    f'{self.name}:\n{self._service.logs().decode()}',
                )
            countdown -= 1
            time.sleep(self._wait_timeout_interval)

    def _teardown_old(self, service_id: str):
        try:
            old = self._client.services.get(service_id)
        except docker.errors.NotFound:
            return
        old.remove()

    def __getattr__(self, attr: Any) -> Any:
        """Passthrough any attribute requests.

        Passthrough requests that `self._service` can provide.
        """
        return getattr(self._service, attr)


@pytest.fixture(scope='function')
def canned_docker_service() -> ServiceWrapper:
    """Return a canned `ServiceWrapper`.

    The service is a vert minimal service that does nothing. It's suitable
    for testing the client's ability to manage Docker services.
    """
    canned = ServiceWrapper(docker.from_env())
    canned.create(
        'alpine:latest',
        name='certdeploy_test_service',
        command='''/bin/sh -c 'while true; do sleep 600; done' ''',
        labels={'certdeploy_test': 'hello'},
    )
    yield canned
    canned.teardown()
