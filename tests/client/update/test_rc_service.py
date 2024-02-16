"""Tests for `certdeploy.client.update.update_rc_service`."""

from typing import Callable

import pytest
from fixtures.rc_service import RCServiceFlags
from fixtures.utils import Script

from certdeploy.client.config import ClientConfig
from certdeploy.client.config.service import RCService
from certdeploy.client.errors import RCServiceError
from certdeploy.client.update import update_rc_service


def test_restarts_rc_service_service(
    tmp_client_config: Callable[[...], ClientConfig],
    tmp_rc_service: Callable[[str, bool], tuple[str, Script]],
):
    """Verify that the service is called correctly.

    The mock service must be called with the restart action and given unit.
    """
    service_name, mock_service = tmp_rc_service()
    client_config = tmp_client_config(
        fail_fast=True, rc_service_exec=str(mock_service.path)
    )
    update_rc_service(
        RCService({'name': service_name, 'action': 'restart'}), client_config
    )
    assert mock_service.flag_text == RCServiceFlags.RESTARTED


def test_reloads_rc_service_service(
    tmp_client_config: Callable[[...], ClientConfig],
    tmp_rc_service: Callable[[str, bool], tuple[str, Script]],
):
    """Verify that the service is called correctly.

    The mock service must be called with the reload action and given unit.
    """
    service_name, mock_service = tmp_rc_service()
    client_config = tmp_client_config(
        fail_fast=True, rc_service_exec=str(mock_service.path)
    )
    update_rc_service(
        RCService({'name': service_name, 'action': 'reload'}), client_config
    )
    assert mock_service.flag_text == RCServiceFlags.RELOADED


def test_fails_fast_when_rc_service_service_fails(
    tmp_client_config: Callable[[...], ClientConfig],
    tmp_rc_service: Callable[[str, bool], tuple[str, Script]],
):
    """Verify that `update_rc_service` fails fast.

    When service returns non-zero `update_rc_service` must raise an
    exception immediately when `fail_fast` is `True`.
    """
    service_name, mock_service_exec = tmp_rc_service(fail=True)
    client_config = tmp_client_config(
        fail_fast=True, rc_service_exec=str(mock_service_exec.path)
    )
    with pytest.raises(RCServiceError):
        update_rc_service(
            RCService({'name': service_name, 'action': 'reload'}), client_config
        )
    assert mock_service_exec.flag_text == RCServiceFlags.FAILED
