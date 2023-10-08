"""Test that verify the CertDeploy Server config fails given bad values."""

import os
from typing import Callable

import pytest
from fixtures.errors import ServerErrors
from fixtures.utils import ConfigContext

from certdeploy.errors import ConfigError
from certdeploy.server.config import ServerConfig


def test_fails_invalid_key(
    tmp_server_config_file: Callable[[...], ConfigContext],
):
    """Verify unexpected config keys cause an error."""
    context = tmp_server_config_file(bad_config=True)
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(context.config_path)
    assert ServerErrors.INVALID_CONFIG_OPTION in str(err)


def test_fails_nonexistent_privkey(
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify a nonexistent `privkey_filename` causes an error."""
    bad_privkey_filename = '/nonexistent/privkey'
    assert not os.path.exists(
        bad_privkey_filename
    ), 'The nonexistent private key exists this test is invalid'
    context = tmp_server_config_file(privkey_filename=bad_privkey_filename)
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(context.config_path)
    assert ServerErrors.format_invalid_value(
        'privkey_filename', bad_privkey_filename
    ) in str(err)


def test_fails_missing_client_configs(
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify an empty `client_configs` causes an error."""
    assert not os.path.exists('/nonexistent/privkey')
    context = tmp_server_config_file(client_configs=[])
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(context.config_path)
    assert ServerErrors.NO_CLIENT_CONFIG in str(err)


def test_fails_invalid_client_key(
    pubkeygen: Callable[[], str],
    tmp_server_config_file: Callable[[...], ConfigContext],
):
    """Verify unexpected client config keys cause an error."""
    context = tmp_server_config_file(
        client_configs=[
            dict(
                address='1.2.3.4',
                domains=['test.example.com'],
                pubkey=pubkeygen(),
                bad_config=True,
            )
        ]
    )
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(context.config_path)
    assert ServerErrors.INVALID_CLIENT_CONFIG_OPTION in str(err)


def test_fails_invalid_client_pubkey(
    pubkeygen: Callable[[], str],
    tmp_server_config_file: Callable[[...], ConfigContext],
):
    """Verify an invalid client `pubkey` causes an error."""
    bad_privkey = 'not a key'
    context = tmp_server_config_file(
        client_configs=[
            dict(
                address='1.2.3.4',
                domains=['test.example.com'],
                pubkey=bad_privkey,
            )
        ]
    )
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(context.config_path)
    assert ServerErrors.format_invalid_value('pubkey', bad_privkey) in str(err)


def test_fails_invalid_push_mode(
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify an invalid `push_mode` causes an error."""
    bad_push_mode = 'Invalid push_mode'
    context = tmp_server_config_file(push_mode=bad_push_mode)
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(context.config_path)
    error_value = ServerErrors.format_invalid_value('push_mode', bad_push_mode)
    assert error_value in str(err)


def test_fails_invalid_push_interval(
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify an invalid `push_interval` causes an error."""
    bad_push_interval = -1
    context = tmp_server_config_file(push_interval=bad_push_interval)
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(context.config_path)
    error_value = ServerErrors.format_invalid_value(
        'push_interval',
        bad_push_interval,
    )
    assert error_value in str(err)


def test_fails_invalid_push_retries(
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify an invalid `push_retries` causes an error."""
    bad_push_retries = -1
    context = tmp_server_config_file(push_retries=bad_push_retries)
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(context.config_path)
    error_value = ServerErrors.format_invalid_value(
        'push_retries',
        bad_push_retries,
    )
    assert error_value in str(err)


def test_fails_invalid_push_retry_interval(
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify an invalid `push_retry_interval` causes an error."""
    bad_push_retry_interval = -1
    context = tmp_server_config_file(
        push_retry_interval=bad_push_retry_interval,
    )
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(context.config_path)
    error_value = ServerErrors.format_invalid_value(
        'push_retry_interval',
        bad_push_retry_interval,
    )
    assert error_value in str(err)


def test_fails_invalid_join_timeout(
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify an invalid `join_timeout` causes an error."""
    bad_join_timeout = -1
    context = tmp_server_config_file(join_timeout=bad_join_timeout)
    with pytest.raises(ConfigError) as err:
        ServerConfig.load(context.config_path)
    error_value = ServerErrors.format_invalid_value(
        'join_timeout',
        bad_join_timeout,
    )
    assert error_value in str(err)
