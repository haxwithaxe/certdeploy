"""Test the file permissions mode parsing."""

from certdeploy.client.config.client import _mode_to_int


def test_permissions_mode_valid():
    """Verify valid input is converted to the correct integer mode."""
    assert _mode_to_int(511) == 511
    assert _mode_to_int('0o777') == 511
    assert _mode_to_int('0777') == 511
    assert _mode_to_int('777') == 511
    assert _mode_to_int('1') == 1


def test_permissions_mode_invalid():
    """Verify invalid output is converted to negative numbers."""
    assert _mode_to_int('9') < 0
    assert _mode_to_int(-1) < 0
    assert _mode_to_int(True) < 0
    assert _mode_to_int(None) < 0
    assert _mode_to_int('') < 0
