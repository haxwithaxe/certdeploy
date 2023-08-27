
import os
import pathlib

from certdeploy.client.config import ClientConfig
from certdeploy.client.config.service import Script
from certdeploy.client.update import update_script


def test_updates_docker_container_by_name(
        tmp_client_config: callable,
        tmp_script: tuple[pathlib.Path, pathlib.Path]
):
    """Verify the client can run a script."""
    config_path, _ = tmp_client_config(fail_fast=True)
    client_config = ClientConfig.load(config_path)
    script_path, flag_file_path = tmp_script
    # Do the thing under test
    update_script(
        Script({'name': str(script_path)}),
        client_config
    )
    assert os.path.exists(flag_file_path)
