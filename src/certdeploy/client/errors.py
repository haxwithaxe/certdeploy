"""Exceptions for use by the CertDeploy client."""

import os
from subprocess import Popen
from typing import Any, Union

from ..errors import CertDeployError


class UpdateError(CertDeployError):
    """Base class for all service update related errors.

    Arguments:
        service: The `certdeploy.client.config.service.Service` with the
            problem.
        message: Either a message string or an exception. An exception will
            be formatted.
        service_name: The name of the service with a problem in the event
            it needs to be different than `service.name`.
    """

    def __init__(
        self,
        service: Any,
        message: Union[Exception, str] = None,  # noqa: D107,E501
        service_name: str = None,
    ):
        if service.name or service_name:
            service_name = f' {service.name or service_name}'
        else:
            service_name = ''
        if isinstance(message, Exception):
            message = f'{message.__class__.__name__}: {message}'
        message = message or ''
        super().__init__(
            f'{service.__class__.__name__}{service_name} failed '
            f'to update: {message}'
        )


class DockerNotFound(UpdateError):
    """Base class for failed docker API searches.

    Arguments:
        service: The `certdeploy.client.config.service.Service` with the
            problem.
        service_name: The name of the service with a problem in the event
            it needs to be different than `service.name`.
    """

    _type: str = None

    def __init__(self, service: Any, service_name: str = None):  # noqa: D107
        message = (
            f'Could not find any docker {self._type} matching the '
            f'following filter: {service.filters}'
        )
        super().__init__(service, message, service_name)


class DockerContainerNotFound(DockerNotFound):
    """Could not find a docker container using the given filters."""

    _type: str = 'container'


class DockerServiceNotFound(DockerNotFound):
    """Could not find a docker service using the given filters."""

    _type: str = 'service'


class DockerError(UpdateError):
    """Base class for docker related errors.

    Arguments:
        service: The `DockerService` object associated with the error.
        message: Either the `Exception` or the error message string. Defaults
            to `None`.
        service_name: The name of the service in the event the name is unclear
            or unavailable from `service`. Defaults to `None`.
    """

    _type = None

    def __init__(
        self,
        service: Any,
        message: Union[Exception, str] = None,  # noqa: D107,E501
        service_name: str = None,
    ):
        # Reverse order from UpdateError because the docker service/container
        #   name may need to override the `service.name` if the error is for a
        #   filter match.
        service_name = service_name or service.name
        super().__init__(
            service,
            f'Error updating docker {self._type} '
            f'{service_name} from filters={service.filters}: '
            f'{message}',
            service_name,
        )


class DockerContainerError(DockerError):
    """Error restarting a docker container."""

    _type = 'container'


class DockerServiceError(DockerError):
    """Error force updating a docker service."""

    _type = 'service'


class RCServiceError(UpdateError):
    """Error updating a traditional init  service.

    Arguments:
        service: The `certdeploy.client.config.service.Service` with the
            problem.
        message: Either a message string or an exception. An exception will
            be formatted.
        stdout: The combined stdout/stderr from the `service` command.
    """

    def __init__(
        self,
        service: Any,
        message: Union[Exception, str] = None,  # noqa: D107,E501
        stdout: str = None,
    ):
        if not message:
            message = (f'Failed to {service.action} rc service '
                       f'{service.name}')  # fmt: skip
        elif isinstance(message, Exception):
            message = f'{type(message).__name__}: {message}'
        if stdout:
            message = f'{message}. Got combined stdout/stderr: \n{stdout}'
        super().__init__(service, message)


class SystemdError(UpdateError):
    """Error updating a systemd unit.

    Arguments:
        service: The `certdeploy.client.config.service.Service` with the
            problem.
        message: Either a message string or an exception. An exception will
            be formatted.
        stdout: The combined stdout/stderr from the systemctl command.
    """

    def __init__(
        self,
        service: Any,
        message: Union[Exception, str] = None,  # noqa: D107,E501
        stdout: str = None,
    ):
        if not message:
            message = (f'Failed to {service.action} systemd unit '
                       f'{service.name}')  # fmt: skip
        elif isinstance(message, Exception):
            message = f'{type(message).__name__}: {message}'
        if stdout:
            message = f'{message}. Got combined stdout/stderr: \n{stdout}'
        super().__init__(service, message)


class ScriptError(UpdateError):
    """Error running an update script.

    Arguments:
        service: The `certdeploy.client.config.service.Service` with the
            problem.
        message: Either a message string or an exception. An exception will
            be formatted.
        proc: The `Popen` object that ran the script.
        stdout: The combined stdout/stderr from the script execution.
    """

    def __init__(
        self,
        service: Any,
        message: Union[Exception, str] = None,  # noqa: D107,E501
        proc: Popen = None,
        stdout: str = None,
    ):
        if not message:
            if proc:
                message = (
                    f'Failed to run the update script {service.name} '
                    f'returned={proc.returncode}'
                )
                if not stdout:
                    stdout_bytes = proc.stdout.read()
                    if stdout_bytes:
                        stdout = stdout_bytes.decode()
            else:
                message = f'Failed to run the update script {service.name}'
        elif isinstance(message, Exception):
            message = f'{type(message).__name__}: {message}'
        if stdout:
            message = f'{message}. Got combined stdout/stderr: \n{stdout}'
        super().__init__(service, message)


class InvalidKey(CertDeployError):
    """Certificate validation error.

    Arguments:
        key_path: The path to the invalid key.
    """

    def __init__(self, key_path: os.PathLike):  # noqa: D107
        super().__init__(f'Invalid key {key_path}')
