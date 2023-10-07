"""Functions that update system services."""

import subprocess

import docker

from . import log
from .config import ClientConfig
from .config.service import DockerContainer, DockerService, Script, SystemdUnit
from .errors import (
    DockerContainerError,
    DockerContainerNotFound,
    DockerServiceError,
    DockerServiceNotFound,
    ScriptError,
    SystemdError,
    UpdateError,
)


def update_docker_container(spec: DockerContainer, client_config: ClientConfig):
    """Update a docker container.

    Arguments:
        spec: The update service specifications.
        client_config: The CertDeploy client config.

    Raises:
        DockerContainerError: When there is a docker error while restarting the
            container.
        DockerContainerNotFound: When the specified container cannot be found.
    """
    log.debug('Updating %s', spec)
    api = docker.DockerClient(base_url=client_config.docker_url)
    matches = api.containers.list(filters=spec.filters)
    if not matches:
        err = DockerContainerNotFound(spec)
        if client_config.fail_fast:
            raise err
        log.error(err)
        return
    for container in matches:
        try:
            container.restart(timeout=spec.timeout)
        except docker.errors.APIError as err:
            error = DockerContainerError(
                spec,
                err,
                str(container.attrs.get('Names')),
            )
            if client_config.fail_fast:
                raise error from err
            log.error(error, exc_info=err)
        else:
            log.info(
                'Docker container updated: names=%s, filters=%s',
                container.attrs.get('Names'),
                spec.filters,
            )


def update_docker_service(spec: DockerService, client_config: ClientConfig):
    """Force update a docker service.

    Arguments:
        spec: The update service specifications.
        client_config: The CertDeploy client config.

    Raises:
        DockerServiceError: When there is a docker error while force updating
            the service.
        DockerServiceNotFound: When the specified service cannot be found.
    """
    log.debug('Updating %s', spec)
    api = docker.DockerClient(base_url=client_config.docker_url)
    if spec.name:
        try:
            matches = [api.services.get(spec.name)]
        except docker.errors.NotFound:
            matches = []
    else:
        matches = api.services.list(filters=spec.filters)
    if not matches:
        # Borrowing the formatting from the exception
        err = DockerServiceNotFound(spec)
        if client_config.fail_fast:
            raise err
        log.error(err)
        return
    for service in matches:
        try:
            warnings = service.force_update()
        except docker.errors.APIError as err:
            # Borrowing the formatting from the exception
            error = DockerServiceError(spec, service_name=service.name)
            if client_config.fail_fast:
                raise error from err
            log.error(error, exc_info=err)
        else:
            for warn in warnings.get('Warnings') or []:
                log.warning('Got warning from the Docker API: %s', warn)
            log.info('Docker service updated: name=%s', service.name)


def update_script(script: Script, client_config: ClientConfig):
    """Update the system with a script.

    Arguments:
        script: The update service specifications.
        client_config: The CertDeploy client config.

    Raises:
        ScriptError: When the script encounters an `OSError`, doesn't finish in
            a timely manner (according to `script.timeout`), or exits non-zero.
    """
    log.debug('Updating %s', script)
    try:
        proc = subprocess.Popen(
            [script.script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        proc.wait(timeout=script.timeout)
    except (OSError, subprocess.TimeoutExpired) as err:
        # Regular errors from the script shouldn't halt the whole
        #   set of updates unless fail_fast is True.
        # Borrowing the exception's formatting.
        error = ScriptError(script, err)
        if client_config.fail_fast:
            raise error from err
        log.error(error, exc_info=err)
        return
    stdout = proc.stdout.read().decode()
    log.debug(
        'Script %s returned=%s, combined stdout/stderr: \n%s',
        script.script_path,
        proc.returncode,
        stdout,
    )
    if proc.returncode != 0:
        # Borrowing the exception's formatting
        err = ScriptError(script, proc=proc, stdout=stdout)
        if client_config.fail_fast:
            raise err
        log.error(err)
    else:
        log.info('Script %s returned=%s', script.script_path, proc.returncode)


def update_systemd_unit(unit: SystemdUnit, client_config: ClientConfig):
    """Update a Systemd unit.

    Arguments:
        unit: The update service specifications.
        client_config: The CertDeploy client config.

    Raises:
        SystemdError: When the systemctl encounters an `OSError`, doesn't
            finish in a timely manner (according to `script.timeout`), or exits
            non-zero.
    """
    log.debug('Updating %s', unit)
    cmd = [client_config.systemd_exec, unit.action, unit.name]
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        proc.wait(timeout=unit.timeout)
    except (OSError, subprocess.TimeoutExpired) as err:
        # Regular errors from the systemctl call shouldn't halt the whole
        #   set of updates unless fail_fast is True.
        # Borrowing the exception's formatting.
        error = SystemdError(unit, err)
        if client_config.fail_fast:
            raise error from err
        log.error(error, exc_info=err)
        return
    stdout = proc.stdout.read().decode()
    log.debug(
        'Systemctl command %s returned=%s. Got combined ' 'stdout/stderr: \n%s',
        proc.returncode,
        cmd,
        stdout,
    )
    if proc.returncode != 0:
        # Borrowing the exception's formatting.
        err = SystemdError(unit, stdout=stdout)
        if client_config.fail_fast:
            raise err
        log.error(err)
    log.info('Systemd unit %s %sed.', unit.name, unit.action)


# An index of Service types to update functions
_UPDATER_MAP = {
    DockerContainer: update_docker_container,
    DockerService: update_docker_service,
    Script: update_script,
    SystemdUnit: update_systemd_unit,
}


def update_services(config: ClientConfig):
    """Update all services in `config.services`.

    Arguments:
        config: The CertDeploy client config.
    """
    for service in config.services:
        try:
            _UPDATER_MAP[type(service)](service, config)
        except UpdateError as err:
            # Don't halt on UpdateError unless fail_fast is True
            # ConfigError and any unexpected errors should halt
            if config.fail_fast:
                raise err from err
