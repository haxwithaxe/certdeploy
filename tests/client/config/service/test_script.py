"""Verify the `Script` update service type is parsed correctly."""

import os
import pathlib
import shutil
from typing import Callable

import pytest
from fixtures.errors import ClientErrors
from fixtures.utils import ConfigContext

from certdeploy.client.config import ClientConfig
from certdeploy.client.config.service import Script
from certdeploy.errors import ConfigError


def test_accepts_absolute_name_values(
    tmp_client_config_file: Callable[[...], ConfigContext],
    tmp_path: pathlib.Path,
):
    """Verify the `script` update service type `name` is parsed.

    Valid `name` values for the `script` update service type that are absolute
    paths are accepted.
    """
    script = tmp_path.joinpath('__this_is_a_test_script.sh')
    script.write_text('')
    context = tmp_client_config_file(
        update_services=[dict(type='script', name=str(script.absolute()))]
    )
    config = ClientConfig.load(context.config_path)
    ref_service = Script(dict(name=str(script.absolute())))
    assert ref_service in config.services
    test_service = config.services[config.services.index(ref_service)]
    assert test_service.script_path == ref_service.script_path


def test_accepts_relative_name_values(
    tmp_client_config_file: Callable[[...], ConfigContext],
    tmp_path: pathlib.Path,
):
    """Verify the `script` update service type `name` is parsed.

    Valid `name` values for the `script` update service type that are relative
    paths are accepted and turned into absolute paths.
    """
    script = tmp_path.joinpath('__this_is_a_test_script.sh')
    script.write_text('')
    cwd = os.curdir
    os.chdir(tmp_path)
    assert not shutil.which(
        script.name
    ), f'{script.name} is in PATH so this test is ambiguous'
    context = tmp_client_config_file(
        update_services=[dict(type='script', name=script.name)]
    )
    config = ClientConfig.load(context.config_path)
    ref_service = Script(dict(name=script.name))
    os.chdir(cwd)
    assert ref_service in config.services
    test_service = config.services[config.services.index(ref_service)]
    assert test_service.script_path == str(script.absolute())


def test_accepts_valid_name_values(
    tmp_client_config_file: Callable[[...], ConfigContext]
):
    """Verify the `script` update service type `name` is parsed.

    Valid `name` values for the `script` update service type that are in `$PATH`
    paths are accepted and turned into absolute paths.
    """
    true_exec_path = shutil.which('true')
    assert true_exec_path, '`true` is not in PATH. This test will always fail.'
    config_filename, _ = tmp_client_config_file(
        update_services=[
            dict(type='script', name='true'),
        ]
    )
    config = ClientConfig.load(config_filename)
    ref_service = Script(dict(name='true'))
    assert ref_service in config.services
    test_service = config.services[config.services.index(ref_service)]
    assert test_service.script_path == true_exec_path


def test_accepts_valid_timeout_int(
    tmp_client_config_file: Callable[[...], ConfigContext],
):
    timeout = 11
    context = tmp_client_config_file(
        update_services=[
            dict(
                type='script',
                name='true',
                timeout=timeout,
            )
        ],
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].timeout == timeout


def test_accepts_valid_timeout_float(
    tmp_client_config_file: Callable[[...], ConfigContext],
):
    timeout = 11.7
    context = tmp_client_config_file(
        update_services=[
            dict(
                type='script',
                name='true',
                timeout=timeout,
            )
        ],
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].timeout == timeout


def test_gets_default_timeout(
    tmp_client_config_file: Callable[[...], ConfigContext],
):
    timeout = 13.37
    context = tmp_client_config_file(
        script_timeout=timeout,
        update_services=[
            dict(
                type='script',
                name='true',
            )
        ],
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].timeout == timeout


def test_overrides_timeout_with_none(
    tmp_client_config_file: Callable[[...], ConfigContext],
):
    context = tmp_client_config_file(
        script_timeout=23,
        update_services=[
            dict(
                type='script',
                name='true',
                timeout=None,
            )
        ],
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].timeout is None


def test_overrides_timeout_with_int(
    tmp_client_config_file: Callable[[...], ConfigContext],
):
    timeout = 37
    context = tmp_client_config_file(
        script_timeout=29,
        update_services=[
            dict(
                type='script',
                name='true',
                timeout=timeout,
            )
        ],
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].timeout == timeout


def test_fails_invalid_name_values(
    tmp_client_config_file: Callable[[...], ConfigContext]
):
    """Verify the `script` update service type `name` is parsed.

    Verify `ConfigError` is thrown for `name` values that are a relative path
    or command, and not in PATH or working directory.
    """
    script_name = '__certdeploy_test_script_that_does_not_exist'
    ## Verify the script is not in the current directory
    assert not os.path.exists(
        script_name
    ), f'There is cruft "{script_name}" in the temp directory "{os.curdir}".'
    ## Verify the script is not in the PATH
    assert not shutil.which(
        script_name
    ), f'{script_name} is in PATH so this test is ambiguous.'
    context = tmp_client_config_file(
        update_services=[dict(type='script', name=script_name)]
    )
    with pytest.raises(ConfigError) as err:
        ClientConfig.load(context.config_path)
    assert ClientErrors.format_missing_script_service(
        script_name, os.path.abspath(script_name)
    ) in str(err)


def test_fails_missing_name_values(
    tmp_client_config_file: Callable[[...], ConfigContext]
):
    """Verify the `script` update service type `name` is parsed.

    Verify `ConfigError` is thrown for `name` values that are `None`.
    """
    context = tmp_client_config_file(
        update_services=[dict(type='script', name=None)],
    )
    with pytest.raises(ConfigError) as err:
        ClientConfig.load(context.config_path)
    error_str = ClientErrors.format_invalid_value(
        'name',
        'None',
        'script config',
    )
    assert error_str in str(err)
