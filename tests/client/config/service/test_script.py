"""Verify the `Script` update service type is parsed correctly."""

import os
import pathlib
import shutil

import py
import pytest

from certdeploy.client.config import ClientConfig
from certdeploy.client.config.service import Script
from certdeploy.errors import ConfigError


def test_accepts_absolute_name_values(tmp_client_config_file: callable,
                                      tmp_path: pathlib.Path):
    """Verify the `script` update service type `name` is parsed.

    Valid `name` values for the `script` update service type that are absolute
    paths are accepted.
    """
    script = tmp_path.joinpath('__this_is_a_test_script.sh')
    script.write_text('')
    context = tmp_client_config_file(
        update_services=[
            dict(type='script', name=str(script.absolute()))
        ]
    )
    config = ClientConfig.load(context.config_path)
    ref_service = Script(dict(name=str(script.absolute())))
    assert ref_service in config.services
    test_service = config.services[config.services.index(ref_service)]
    assert test_service.script_path == ref_service.script_path


def test_accepts_relative_name_values(tmp_client_config_file: callable,
                                      tmp_path: pathlib.Path):
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
        update_services=[
            dict(type='script', name=script.name)
        ]
    )
    config = ClientConfig.load(context.config_path)
    ref_service = Script(dict(name=script.name))
    os.chdir(cwd)
    assert ref_service in config.services
    test_service = config.services[config.services.index(ref_service)]
    assert test_service.script_path == str(script.absolute())


def test_accepts_valid_name_values(tmp_client_config_file: callable):
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


def test_fails_invalid_name_values(tmp_client_config_file: callable,
                                   tmpdir: py.path.local):
    """Verify the `script` update service type `name` is parsed.

    Verify `ConfigError` is thrown for `name` values that are a relative path
    or command, and not in PATH or working directory.
    """
    script_name = '__certdeploy_test_script_that_does_not_exist'
    ## Verify the script is not in the current directory
    assert not os.path.exists(script_name), \
        f'There is cruft "{script_name}" in the tmpdir "{tmpdir}".'
    ## Verify the script is not in the PATH
    assert not shutil.which(script_name), \
        f'{script_name} is in PATH so this test is ambiguous.'
    context = tmp_client_config_file(
        update_services=[
            dict(type='script', name=script_name)
        ]
    )
    with pytest.raises(ConfigError) as err:
        ClientConfig.load(context.config_path)
    assert (f'Script file "{os.path.abspath(script_name)}" for service '
            f'{script_name} not found.') in str(err)


def test_fails_missing_name_values(tmp_client_config_file: callable,
                                   tmpdir: py.path.local):
    """Verify the `script` update service type `name` is parsed.

    Verify `ConfigError` is thrown for `name` values that are `None`.
    """
    context = tmp_client_config_file(
        update_services=[
            dict(type='script', name=None)
        ]
    )
    with pytest.raises(ConfigError) as err:
        ClientConfig.load(context.config_path)
    assert 'Invalid value "None" for script config `name`.' in str(err)
