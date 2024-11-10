"""Verify the `DockerContainer` service type is parsed correctly."""

from typing import Callable

from fixtures.utils import ConfigContext

from certdeploy.client.config import ClientConfig
from certdeploy.client.config.service import DockerContainer


def test_accepts_and_transforms_valid_name(
    tmp_client_config_file: Callable[[...], ConfigContext]
):
    """Verify the `docker_container` update service type `name` is parsed.

    Valid values for `docker_container` are accepted and `name` is converted to
    the `filters`.
    """
    container_name = 're-test_container.8'
    context = tmp_client_config_file(
        update_services=[
            dict(type='docker_container', name=container_name),
        ]
    )
    config = ClientConfig.load(context.config_path)
    ref_service = DockerContainer(dict(name=container_name))
    assert ref_service in config.services
    service = config.services[config.services.index(ref_service)]
    assert service.filters['name'] == f'^{container_name}$'


def test_config_update_services_docker_container_filters(
    tmp_client_config_file: Callable[[...], ConfigContext]
):
    """Verify the `docker_container` update service type `filters` is parsed.

    Valid values for the `docker_container` update service type
    are accepted and the filters are transferred correctly.
    """
    filter_name = 'filter_name'
    context = tmp_client_config_file(
        update_services=[
            dict(type='docker_container', filters={'name': filter_name}),
        ]
    )
    config = ClientConfig.load(context.config_path)
    ref_service = DockerContainer(dict(filters={'name': filter_name}))
    assert ref_service in config.services
    service = config.services[config.services.index(ref_service)]
    assert service.filters['name'] == filter_name


def test_accepts_valid_timeout(
    tmp_client_config_file: Callable[[...], ConfigContext],
):
    """Verify the `docker_container` update service type `timeout` is parsed."""
    timeout = 97
    context = tmp_client_config_file(
        update_services=[
            dict(
                type='docker_container',
                name='timeout-test_container',
                timeout=timeout,
            ),
        ]
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].timeout == timeout


def test_gets_default_timeout(
    tmp_client_config_file: Callable[[...], ConfigContext],
):
    """Verify the `docker_container` gets the default from `docker_timeout`."""
    timeout = 83
    context = tmp_client_config_file(
        docker_timeout=timeout,
        update_services=[
            dict(
                type='docker_container',
                name='timeout-test_container',
            ),
        ],
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].timeout == timeout


def test_overrides_default_timeout_with_none(
    tmp_client_config_file: Callable[[...], ConfigContext]
):
    """Verify the `docker_container` overrides the default.

    Verify the default is overridden with `None` when the value of `timeout`
    is `False`.
    """
    context = tmp_client_config_file(
        docker_timeout=89,
        update_services=[
            dict(
                type='docker_container',
                name='timeout-test_container',
                timeout=None,
            ),
        ],
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].timeout is None


def test_overrides_default_timeout_with_int(
    tmp_client_config_file: Callable[[...], ConfigContext]
):
    """Verify the `docker_container` overrides the default.

    Verify the default is overridden with the value of `timeout` when the value
    is and `int`.
    """
    timeout = 23
    context = tmp_client_config_file(
        docker_timeout=79,
        update_services=[
            dict(
                type='docker_container',
                name='timeout-test_container',
                timeout=timeout,
            ),
        ],
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].timeout == timeout
