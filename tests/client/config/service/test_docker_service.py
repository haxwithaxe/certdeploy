
from certdeploy.client.config import ClientConfig
from certdeploy.client.config.service import DockerService


def test_accepts_and_transforms_valid_name(tmp_client_config_file: callable):
    """Verify the valid values for the `docker_service` update service type
    are accepted and `name` is converted to the `filters`.
    """
    service_name = 're-test_container.8'
    config_filename, _ = tmp_client_config_file(
        update_services=[
            dict(type='docker_service', name=service_name),
        ]
    )
    config = ClientConfig.load(config_filename)
    ref_service = DockerService(dict(name=service_name))
    assert ref_service in config.services
    service = config.services[config.services.index(ref_service)]
    assert service.filters['name'] == f'^{service_name}$'


def test_accepts_valid_filters(tmp_client_config_file: callable):
    """Verify the valid values for the `docker_service` update service type
    are accepted and the filters are transferred correctly.
    """
    filter_name = 'filter_name'
    config_filename, _ = tmp_client_config_file(
        # In the order Systemd lists them
        update_services=[
            dict(type='docker_service', filters={'name': filter_name}),
        ]
    )
    config = ClientConfig.load(config_filename)
    ref_service = DockerService(dict(filters={'name': filter_name}))
    assert ref_service in config.services
    test_service = config.services[config.services.index(ref_service)]
    assert test_service.filters['name'] == filter_name
