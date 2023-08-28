
import pathlib

import pytest
import yaml

from certdeploy.client.config import ClientConfig


@pytest.fixture(scope='function')
def tmp_client_config_file(tmp_path: pathlib.Path) -> callable:
    src = tmp_path.joinpath('src')
    src.mkdir()
    dest = tmp_path.joinpath('dest')
    dest.mkdir()
    config_filename = tmp_path.joinpath('client.yml')
    # Non-default values for top level options
    config = dict(
        destination=str(dest),
        source=str(src),
        sftpd={},
        systemd_exec='test systemd_exec value',
        systemd_timeout=42,
        docker_url='test docker_url value',  # Use the local socket
        update_services=[],
        update_delay='11s'
    )

    def set_config(**conf):
        config.update(conf)
        yaml.safe_dump(config, config_filename.open('w'))
        return config_filename, config

    return set_config


@pytest.fixture(scope='function')
def tmp_client_config(tmp_path_factory: pytest.TempPathFactory) -> callable:

    def _get_config(**conf) -> ClientConfig:
        tmp_path = tmp_path_factory.mktemp('client_config')
        src = tmp_path.joinpath('src')
        src.mkdir()
        dest = tmp_path.joinpath('dest')
        dest.mkdir()
        config_filename = tmp_path.joinpath('client.yml')
        # Non-default values for top level options
        config = dict(
            destination=str(dest),
            source=str(src)
        )
        config.update(conf)
        yaml.safe_dump(config, config_filename.open('w'))
        return ClientConfig.load(config_filename)

    return _get_config
