"""Fixtures an utilities for testing client Systemd unit updating."""

from typing import Callable

import pytest
from fixtures.utils import Script


class SystemdFlags:
    """Flag strings to write in the flag file."""

    FAILED = 'failed'
    INITIALIZED = 'initialized'
    RELOADED = 'reloaded'
    RESTARTED = 'restarted'


"""This script template has the following behaviors:
* Verifies that A valid action is given.
    * When the reload action is given the corresponding string is written to
        the flag file.
    * When the restart action is given the corresponding string is written to
        the flag file.
* Verifies that the appropriate unit name is given. Nothing additional is
    written to the flag file in the event the unit name is correct.
* When it fails it writes 'failed' to the flag file.
"""
MOCK_SYSTEMCTL_TEMPLATE = f'''\
#!/bin/bash

set -e

{{fail}}

# Verify a valid action is given
case $1 in
    restart)
        echo {SystemdFlags.RESTARTED} > "{{flag_file_path}}"
        ;;
    reload)
        echo {SystemdFlags.RELOADED} > "{{flag_file_path}}"
        ;;
    *)
        echo Invalid action $1
        echo {SystemdFlags.FAILED} > "{{flag_file_path}}"
        exit 1
        ;;
esac

# Verify the unit name given is the right unit name
if [[ "$2" != "{{unit_name}}" ]]; then
    echo Invalid unit name $2
    echo {SystemdFlags.FAILED} > "{{flag_file_path}}"
    exit 2
fi
'''


@pytest.fixture(scope='function')
def tmp_systemd_service(tmp_script: Callable[[str, str, str, str], Script]
                        ) -> Callable[[str, bool], tuple[str, Script]]:
    """Return a factory for temporary systemctl expecting a unit name."""

    def _tmp_systemd_service(unit_name: str = 'certdeploy-test.service',
                             fail: bool = False) -> tuple[str, Script]:
        """Return a unit name and mock systemctl.

        Arguments:
            unit_name: The desired unit name. Defaults to
                'certdeploy-test.service'.
            fail: If True a command is inserted into the mock systemctl that
                causes premature failure. Defaults to `False`

        Returns:
            A unit name the mock systemctl is expecting and the script object
            for the mock systemctl.
        """
        fail_str = ''
        if fail:
            # The guaranteed fail mode command
            fail_str = (f'echo {SystemdFlags.FAILED} > '
                        '{flag_file_path}; exit 3')
        # Create a mock systemctl that will detect if the right args are
        #   passed.
        mock_systemctl = tmp_script(
            'mock-systemctl',
            MOCK_SYSTEMCTL_TEMPLATE,
            unit_name=unit_name,
            fail=fail_str
        )
        # The tests expects the file to exist so a neutral payload is written to
        #   it.
        mock_systemctl.flag_file.write_text(SystemdFlags.INITIALIZED)
        return unit_name, mock_systemctl

    return _tmp_systemd_service
