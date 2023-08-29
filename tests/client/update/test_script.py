
import conftest

from certdeploy.client.config.service import Script
from certdeploy.client.update import update_script


def test_updates_with_script(
        tmp_client_config: callable,
        tmp_script_for_service: conftest.Script
):
    """Verify the client can run a script."""
    client_config = tmp_client_config(fail_fast=True)
    script = tmp_script_for_service
    # Do the thing under test
    update_script(
        Script({'name': str(script.path)}),
        client_config
    )
    assert script.flag_file.exists()
