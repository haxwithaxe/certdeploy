"""Tests to verify the certdeploy.client.deploy._set_permissions works."""

import os
import pathlib

import pytest

from certdeploy.client.deploy import _set_permissions


def test_all_none_values_does_nothing(tmp_path: pathlib.Path):
    test_file = tmp_path.joinpath('test.pem')
    test_file.write_text('')
    stat_before = test_file.stat()
    _set_permissions(test_file.absolute(), None, None, None)
    assert stat_before == test_file.stat()


def test_sets_mode_when_given(tmp_path: pathlib.Path):
    mode_before = 33206
    mode_after = 33188
    mode_arg = 0o644
    test_file = tmp_path.joinpath('test.pem')
    test_file.write_text('')
    os.chmod(test_file.absolute(), mode_before)
    stat_before = test_file.stat()
    assert (
        stat_before.st_mode == mode_before
    ), 'The mode was not set correctly in the test setup'
    _set_permissions(test_file.absolute(), mode_arg, None, None)
    stat_after = test_file.stat()
    assert stat_before != stat_after
    assert stat_before.st_gid == stat_after.st_gid
    assert stat_before.st_uid == stat_after.st_uid
    assert mode_after == stat_after.st_mode


def test_tries_set_owner_when_given(tmp_path: pathlib.Path):
    test_file = tmp_path.joinpath('test.pem')
    test_file.write_text('')
    # First try to set the owner to the current user (aka current owner)
    #  This should be a noop and won't error out.
    stat_before = test_file.stat()
    _set_permissions(test_file.absolute(), None, stat_before.st_uid, None)
    stat_after = test_file.stat()
    assert stat_before.st_gid == stat_after.st_gid
    assert stat_before.st_uid == stat_after.st_uid
    assert stat_before.st_mode == stat_after.st_mode
    # Next try to set the owner to another user (root)
    #   This should throw a permissions error proving the code is called and the
    #   previous step successfully "changed" the owner to the only owner this
    #   user has permissions to change to.
    with pytest.raises(PermissionError):
        _set_permissions(test_file.absolute(), None, 0, None)


def test_tries_set_group_when_given(tmp_path: pathlib.Path):
    test_file = tmp_path.joinpath('test.pem')
    test_file.write_text('')
    # First try to set the group to the current user's group (aka current
    #  group). This should be a noop and won't error out.
    stat_before = test_file.stat()
    _set_permissions(test_file.absolute(), None, None, stat_before.st_gid)
    stat_after = test_file.stat()
    assert stat_before.st_gid == stat_after.st_gid
    assert stat_before.st_uid == stat_after.st_uid
    assert stat_before.st_mode == stat_after.st_mode
    # Next try to set the group to another group (root)
    #   This should throw a permissions error proving the code is called and the
    #   previous step successfully "changed" the group to the only group this
    #   user has permissions to change to.
    with pytest.raises(PermissionError):
        _set_permissions(test_file.absolute(), None, None, 0)
