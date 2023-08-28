
from certdeploy.client.config import ClientConfig
from certdeploy.client.config.service import DockerContainer


def test_accepts_and_transforms_valid_name(tmp_client_config_file: callable):
    """Verify the valid values for the `docker_container` update service type
    are accepted and `name` is converted to the `filters`.
    """
    container_name = 're-test_container.8'
    config_filename, _ = tmp_client_config_file(
        update_services=[
            dict(type='docker_container', name=container_name),
        ]
    )
    config = ClientConfig.load(config_filename)
    ref_service = DockerContainer(dict(name=container_name))
    assert ref_service in config.services
    service = config.services[config.services.index(ref_service)]
    assert service.filters['name'] == f'^{container_name}$'


def test_config_update_services_docker_container_filters(
        tmp_client_config_file: callable
):
    """Verify the valid values for the `docker_container` update service type
    are accepted and the filters are transferred correctly.
    """
    filter_name = 'filter_name'
    config_filename, _ = tmp_client_config_file(
        update_services=[
            dict(type='docker_container', filters={'name': filter_name}),
        ]
    )
    config = ClientConfig.load(config_filename)
    ref_service = DockerContainer(dict(filters={'name': filter_name}))
    assert ref_service in config.services
    service = config.services[config.services.index(ref_service)]
    assert service.filters['name'] == filter_name
