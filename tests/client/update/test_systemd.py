
import pytest
from conftest import SystemdFlags

from certdeploy.client.config.service import SystemdUnit
from certdeploy.client.update import update_systemd_unit
from certdeploy.errors import CertDeployError


def test_restarts_systemd_service(tmp_client_config: callable,
                                  tmp_systemd_service: callable):
    """Verify that the systemctl is called correctly.

    The mock systemctl must be called with the restart action and given unit.
    """
    unit_name, mock_systemctl = tmp_systemd_service()
    client_config = tmp_client_config(
        fail_fast=True,
        systemd_exec=str(mock_systemctl.path)
    )
    update_systemd_unit(
        SystemdUnit({'name': unit_name, 'action': 'restart'}),
        client_config
    )
    assert mock_systemctl.flag_text == SystemdFlags.RESTARTED.value


def test_reloads_systemd_service(tmp_client_config: callable,
                                 tmp_systemd_service: callable):
    """Verify that the systemctl is called correctly.

    The mock systemctl must be called with the reload action and given unit.
    """
    unit_name, mock_systemctl = tmp_systemd_service()
    client_config = tmp_client_config(
        fail_fast=True,
        systemd_exec=str(mock_systemctl.path)
    )
    update_systemd_unit(
        SystemdUnit({'name': unit_name, 'action': 'reload'}),
        client_config
    )
    assert mock_systemctl.flag_text == SystemdFlags.RELOADED.value


def test_fails_fast_when_systemd_service_fails(tmp_client_config: callable,
                                               tmp_systemd_service: callable):
    """Verify that `update_systemd_unit` fails fast.

    When systemctl returns non-zero `update_systemd_unit` must raise an
    exception immediately when `fail_fast` is `True`.
    """
    unit_name, mock_systemctl = tmp_systemd_service(fail=True)
    client_config = tmp_client_config(
        fail_fast=True,
        systemd_exec=str(mock_systemctl.path)
    )
    with pytest.raises(CertDeployError):
        update_systemd_unit(
            SystemdUnit({'name': unit_name, 'action': 'reload'}),
            client_config
        )
    assert mock_systemctl.flag_text == SystemdFlags.FAILED.value
