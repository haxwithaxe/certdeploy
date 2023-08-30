"""Temporary client config fixtures."""

import pathlib
from typing import Any

import pytest
import yaml

from certdeploy.client.config import ClientConfig


@pytest.fixture(scope='function')
def tmp_client_config_file(tmp_path: pathlib.Path) -> callable:
    """Return a temporary client config constructor."""
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

    def _tmp_client_config_file(**conf: Any) -> tuple[pathlib.Path, dict]:
        """Finish configuring the temporary client config.

        Keyword Arguments:
            conf: Key value pairs corresponding to
                `certdeploy.client.config.client.Config` arguments.
        Returns:
            pathlib.Path, dict: The path of the client config and the `dict`
                used to create it.
        """
        config.update(conf)
        yaml.safe_dump(config, config_filename.open('w'))
        return config_filename, config

    return _tmp_client_config_file


@pytest.fixture(scope='function')
def tmp_client_config(tmp_path_factory: pytest.TempPathFactory) -> callable:
    """Return a temporary client config constructor."""

    def _tmp_client_config(**conf) -> ClientConfig:
        """Finish configuring the temporary client config.

        Keyword Arguments:
            conf: Key value pairs corresponding to
                `certdeploy.client.config.client.Config` arguments.

        Returns:
            ClientConfig: The client config with the given values.
        """
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

    return _tmp_client_config
