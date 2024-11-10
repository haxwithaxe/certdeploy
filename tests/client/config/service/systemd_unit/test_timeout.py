"""Verify the Systemd service `action` config behaves as expected."""

from typing import Callable

from fixtures.utils import ConfigContext

from certdeploy.client.config import ClientConfig


def test_accepts_valid_timeout_int(
    tmp_client_config_file: Callable[[...], ConfigContext]
):
    """Verify an `int` value for the `timeout` config is parsed."""
    name = 'timeout-test.service'
    timeout = 91
    config_filename, _ = tmp_client_config_file(
        update_services=[
            dict(type='systemd', name=name, timeout=timeout),
        ]
    )
    config = ClientConfig.load(config_filename)
    assert config.services[0].name == name
    assert config.services[0].timeout == timeout


def test_accepts_valid_timeout_float(
    tmp_client_config_file: Callable[[...], ConfigContext]
):
    """Verify an `float` value for the `timeout` config is parsed."""
    name = 'timeout-test.service'
    timeout = 117.9
    config_filename, _ = tmp_client_config_file(
        update_services=[
            dict(type='systemd', name=name, timeout=timeout),
        ]
    )
    config = ClientConfig.load(config_filename)
    assert config.services[0].name == name
    assert config.services[0].timeout == timeout


def test_gets_default_timeout(
    tmp_client_config_file: Callable[[...], ConfigContext],
):
    """Verify an `int` value for the `timeout` config is parsed."""
    name = 'timeout-test.service'
    timeout = 331
    config_filename, _ = tmp_client_config_file(
        init_timeout=timeout,
        update_services=[
            dict(type='systemd', name=name),
        ],
    )
    config = ClientConfig.load(config_filename)
    assert config.services[0].name == name
    assert config.services[0].timeout == timeout


def test_overrides_default_timeout_with_none(
    tmp_client_config_file: Callable[[...], ConfigContext]
):
    """Verify an `int` value for the `timeout` config is parsed."""
    name = 'timeout-test.service'
    config_filename, _ = tmp_client_config_file(
        init_timeout=113,
        update_services=[
            dict(type='systemd', name=name, timeout=None),
        ],
    )
    config = ClientConfig.load(config_filename)
    assert config.services[0].name == name
    assert config.services[0].timeout is None


def test_overrides_default_timeout_with_int(
    tmp_client_config_file: Callable[[...], ConfigContext]
):
    """Verify an `int` value for the `timeout` config is parsed."""
    name = 'timeout-test.service'
    timeout = 31
    config_filename, _ = tmp_client_config_file(
        init_timeout=131,
        update_services=[
            dict(type='systemd', name=name, timeout=timeout),
        ],
    )
    config = ClientConfig.load(config_filename)
    assert config.services[0].name == name
    assert config.services[0].timeout == timeout
