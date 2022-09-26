
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
    UpdateError
)


def update_docker_container(container: DockerContainer,
                            client_config: ClientConfig):
    log.debug('Updating %s', container)
    api = docker.APIClient(client_config.docker_url)
    matches = api.containers(filters=container.filters)
    if not matches:
        err = DockerContainerNotFound(container)
        if client_config.fail_fast:
            raise err
        log.error(err)
        return
    for match in matches:
        try:
            api.restart(match.get('Id'), timeout=container.timeout)
        except docker.errors.APIError as err:
            error = DockerContainerError(container, err,
                                         str(match.get('Names')))
            if client_config.fail_fast:
                raise error from err
            log.error(error, exc_info=err)
        else:
            log.info('Docker container updated: names=%s, filters=%s',
                     match.get('Names'), container.filters)


def update_docker_service(service: DockerService, client_config: ClientConfig):
    log.debug('Updating %s', service)
    api = docker.APIClient(base_url=client_config.docker_url)
    matches = api.services(filters=service.filters)
    if not matches:
        # Borrowing the formatting from the exception
        err = DockerServiceNotFound(service)
        if client_config.fail_fast:
            raise err
        log.error(err)
        return
    for match in matches:
        service_model = docker.models.services.Service(
            attrs=match,
            client=docker.DockerClient(base_url=client_config.docker_url)
        )
        try:
            warnings = service_model.force_update()
        except docker.errors.APIError as err:
            # Borrowing the formatting from the exception
            error = DockerServiceError(service, service_name=service_model.name)
            if client_config.fail_fast:
                raise UpdateError(error) from err
            log.error(error, exc_info=err)
        else:
            for warn in warnings.get('Warnings') or []:
                log.warning('Got warning from the Docker API: %s', warn)
            log.info('Docker service updated: name=%s',
                     service_model.name)


def update_script(script: Script, client_config: ClientConfig):
    log.debug('Updating %s', script)
    try:
        # pylint: disable=consider-using-with
        proc = subprocess.Popen([script.script_path], stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        # pylint: enable=consider-using-with
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
    log.debug('Script %s returned=%s, combined stdout/stderr: \n%s',
              script.script_path, proc.returncode, stdout)
    if proc.returncode != 0:
        # Borrowing the exception's formatting
        err = ScriptError(script, proc=proc, stdout=stdout)
        if client_config.fail_fast:
            raise err
        log.error(err)
    else:
        log.info('Script %s returned=%s',
                 script.script_path, proc.returncode)


def update_systemd_unit(unit: SystemdUnit, client_config: ClientConfig):
    """Update a Systemd unit."""
    log.debug('Updating %s', unit)
    cmd = [client_config.systemd_exec, unit.action, unit.name]
    try:
        # pylint: disable=consider-using-with
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        proc.wait(timeout=unit.timeout)
        # pylint: enable=consider-using-with
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
    log.debug('Systemctl command %s returned=%s. Got combined '
              'stdout/stderr: \n%s', proc.returncode, cmd, stdout)
    if proc.returncode != 0:
        # Borrowing the exception's formatting.
        err = SystemdError(unit, stdout=stdout)
        if client_config.fail_fast:
            raise err
        log.error(err)
    log.info('Systemd unit %s %sed.', unit.name, unit.action)


_UPDATER_MAP = {
    DockerContainer: update_docker_container,
    DockerService: update_docker_service,
    Script: update_script,
    SystemdUnit: update_systemd_unit
}


def update_services(config: ClientConfig):
    """Update services in `config.services`."""
    for service in config.services:
        try:
            _UPDATER_MAP[type(service)](service, config)
        except UpdateError as err:
            # Don't halt on UpdateError unless fail_fast is True
            # ConfigError and any unexpected errors should halt
            if config.fail_fast:
                raise err from err
