"""Verify the Systemd service `action` config behaves as expected."""

from typing import Callable

from fixtures.utils import ConfigContext

from certdeploy.client.config import ClientConfig
from certdeploy.client.config.service import SystemdUnit


def test_accepts_valid_action_reload(
    tmp_client_config_file: Callable[[...], ConfigContext]
):
    """Verify the `'reload'` value for the `action` config is parsed."""
    name = 'action-test.service'
    action = 'reload'
    config_filename, _ = tmp_client_config_file(
        update_services=[
            dict(type='systemd', name=name,
                 action=action),
        ]
    )
    config = ClientConfig.load(config_filename)
    assert config.services[0].name == name
    assert config.services[0].action == action


def test_accepts_valid_action_restart(
    tmp_client_config_file: Callable[[...], ConfigContext]
):
    """Verify the `'restart'` value for the `action` config is parsed."""
    name = 'action-test.service'
    action = 'restart'
    config_filename, _ = tmp_client_config_file(
        update_services=[
            dict(type='systemd', name=name,
                 action=action),
        ]
    )
    config = ClientConfig.load(config_filename)
    assert config.services[0].name == name
    assert config.services[0].action == action


def test_accepts_valid_action_none(
    tmp_client_config_file: Callable[[...], ConfigContext]
):
    """Verify the `None` value for the `action` config is translated.

    The `None` value for the `action` config in the file produces the default
    action (see `SystemdUnit.action`).
    """
    name = 'action-test.service'
    action = None
    config_filename, _ = tmp_client_config_file(
        update_services=[
            dict(type='systemd', name=name,
                 action=action),
        ]
    )
    config = ClientConfig.load(config_filename)
    assert config.services[0].name == name
    assert config.services[0].action == SystemdUnit.action


def test_accepts_valid_action_empty(
    tmp_client_config_file: Callable[[...], ConfigContext]
):
    """Verify the `''` value for the `action` config is translated.

    The `''` value for the `action` config in the file produces the default
    action (see `SystemdUnit.action`).
    """
    name = 'action-test.service'
    action = ''
    config_filename, _ = tmp_client_config_file(
        update_services=[
            dict(type='systemd', name=name,
                 action=action),
        ]
    )
    config = ClientConfig.load(config_filename)
    assert config.services[0].name == name
    assert config.services[0].action == SystemdUnit.action
