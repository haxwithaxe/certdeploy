"""Tests for the `fail_fast` config in push operations."""

from typing import Callable

import pytest
from fixtures.utils import Script

from certdeploy.errors import CertDeployError
from certdeploy.server.config import ServerConfig
from certdeploy.server.renew import renew_certs


def test_runs_renew_command(
    mock_certbot: Callable[[], Script],
    tmp_server_config: Callable[[...], ServerConfig],
):
    """Verify that the renew_exec is called with the right args."""
    mock_certbot = mock_certbot()
    ## Setup server config
    server_config = tmp_server_config(
        renew_exec=str(mock_certbot.path),
        fail_fast=True,
    )
    ## Run the thing under test
    renew_certs(server_config)
    assert mock_certbot.flag_file.exists()


def test_fail_fast_fails_renew_command(
    mock_certbot: Callable[[], Script],
    tmp_server_config: Callable[[...], ServerConfig],
):
    """Verify that the `renew_certs()` function fails fast."""
    mock_certbot = mock_certbot()
    ## Setup server config
    server_config = tmp_server_config(
        renew_exec=str(mock_certbot.path),
        renew_args=['bad', 'args'],
        fail_fast=True,
    )
    ## Run the thing under test
    with pytest.raises(CertDeployError):
        renew_certs(server_config)
    assert not mock_certbot.flag_file.exists()
