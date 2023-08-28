
from conftest import SystemdFlags

from certdeploy.client.config.service import SystemdUnit
from certdeploy.client.update import update_systemd_unit


def test_restarts_systemd_service(tmp_client_config: callable,
                                  tmp_systemd_service: callable):
    """Verify that the systemctl is called correctly.

    The mock systemctl must be called with the restart action and given unit.
    """
    flag_file_path, unit_name, mock_systemctl_path = tmp_systemd_service()
    client_config = tmp_client_config(
        fail_fast=True,
        systemd_exec=str(mock_systemctl_path)
    )
    update_systemd_unit(
        SystemdUnit({'name': unit_name, 'action': 'restart'}),
        client_config
    )
    assert SystemdFlags.RESTARTED.value == flag_file_path.read_text().strip()


def test_reloads_systemd_service(tmp_client_config: callable,
                                 tmp_systemd_service: callable):
    """Verify that the systemctl is called correctly.

    The mock systemctl must be called with the reload action and given unit.
    """
    flag_file_path, unit_name, mock_systemctl_path = tmp_systemd_service()
    client_config = tmp_client_config(
        fail_fast=True,
        systemd_exec=str(mock_systemctl_path)
    )
    update_systemd_unit(
        SystemdUnit({'name': unit_name, 'action': 'reload'}),
        client_config
    )
    assert SystemdFlags.RELOADED.value == flag_file_path.read_text().strip()
