
import os
import pathlib

from certdeploy.client.config.service import Script
from certdeploy.client.update import update_script


def test_updates_with_script(
        tmp_client_config: callable,
        tmp_script: tuple[pathlib.Path, pathlib.Path]
):
    """Verify the client can run a script."""
    client_config = tmp_client_config(fail_fast=True)
    script_path, flag_file_path = tmp_script
    # Do the thing under test
    update_script(
        Script({'name': str(script_path)}),
        client_config
    )
    assert os.path.exists(flag_file_path)
