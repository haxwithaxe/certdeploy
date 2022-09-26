
import os

import pytest
import yaml


@pytest.fixture(scope='function')
def tmp_client_config(tmp_path_factory: pytest.TempPathFactory) -> callable:
    base_dir = tmp_path_factory.mktemp('conf')
    src = os.path.join(base_dir, 'src')
    os.makedirs(src, exist_ok=True)
    dest = os.path.join(base_dir, 'dest')
    os.makedirs(dest, exist_ok=True)
    config_filename = os.path.join(base_dir, 'client.yml')
    # Non-default values for top level options
    config = dict(
        destination=dest,
        source=src,
        sftpd={},
        systemd_exec='test systemd_exec value',
        systemd_timeout=42,
        docker_url='test docker_url value',  # Use the local socket
        update_services=[],
        update_delay='11s'
    )

    def set_config(**conf):
        config.update(conf)
        with open(config_filename, 'w') as config_file:
            yaml.safe_dump(config, config_file)
        return config_filename, config

    return set_config
