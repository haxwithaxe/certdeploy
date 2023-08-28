
import shutil

import py
import pytest

from certdeploy.client.config import ClientConfig
from certdeploy.client.config.service import Script
from certdeploy.errors import ConfigError


def test_accepts_absolute_name_values(tmp_client_config_file: callable,
                                      tmpdir: py.path.local):
    """Verify the valid values for the `script` update service type are
    accepted.
    """
    abs_test_script = tmpdir.join('__this_is_a_test_script.sh')
    # Not running it but it's got to be written to so might as well make is
    #   real
    abs_test_script.write('#!/bin/sh\n/bin/true')
    config_filename, _ = tmp_client_config_file(
        update_services=[
            dict(type='script', name=str(abs_test_script))
        ]
    )
    config = ClientConfig.load(config_filename)
    ref_service = Script(dict(name=str(abs_test_script)))
    assert ref_service in config.services
    test_service = config.services[config.services.index(ref_service)]
    assert test_service.script_path == ref_service.script_path


def test_accepts_relative_name_values(tmp_client_config_file: callable,
                                      tmpdir: py.path.local):
    """Verify the valid values for the `script` update service type are
    accepted.
    """
    abs_test_script = tmpdir.join('__this_is_a_test_script.sh')
    # If the script is somehow in the path this test is ambiguous.
    assert not shutil.which(
        abs_test_script.basename
    ), f'{abs_test_script} is in PATH so this test is ambiguous'
    # Not running it but it's got to be written to so might as well make is
    #   real
    abs_test_script.write('#!/bin/sh\n/bin/true')
    with tmpdir.as_cwd():
        config_filename, _ = tmp_client_config_file(
            # In the order Systemd lists them
            update_services=[
                dict(type='script', name=abs_test_script.basename)
            ]
        )
        config = ClientConfig.load(config_filename)
        ref_service = Script(dict(name=abs_test_script.basename))
        assert ref_service in config.services
        test_service = config.services[config.services.index(ref_service)]
        assert test_service.script_path == str(abs_test_script)


def test_accepts_valid_name_values(tmp_client_config_file: callable):
    """Verify the valid values for the `script` update service type are
    accepted.
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
    """Verify ConfigError is thrown for `name` values that are a relative path
    or command, and not in PATH or working directory.
    """
    abs_test_script = tmpdir.join('__this_is_a_test_script.sh')
    assert not abs_test_script.exists(), (f'There is cruft "{abs_test_script}" '
                                          'in the tmpdir "{tmpdir}".')
    # If the script is somehow in the path this test is ambiguous.
    assert not shutil.which(
        abs_test_script.basename
    ), f'{abs_test_script} is in PATH so this test is ambiguous.'
    # Running in the tmpdir even though this isn't testing relative names
    #   because we just verified the script isn't in it.
    with tmpdir.as_cwd():
        config_filename, _ = tmp_client_config_file(
            update_services=[
                dict(type='script', name=abs_test_script.basename)
            ]
        )
        with pytest.raises(ConfigError) as err:
            ClientConfig.load(config_filename)
        assert (f'Script file "{abs_test_script}" for service '
                f'{abs_test_script.basename} not found.') in str(err)


def test_fails_missing_name_values(tmp_client_config_file: callable,
                                   tmpdir: py.path.local):
    """Verify ConfigError is thrown for `name` values that are a relative path
    or command, and not in PATH or working directory.
    """
    config_filename, _ = tmp_client_config_file(
        update_services=[
            dict(type='script', name=None)
        ]
    )
    with pytest.raises(ConfigError) as err:
        ClientConfig.load(config_filename)
    assert 'Invalid value "None" for script config `name`.' in str(err)
