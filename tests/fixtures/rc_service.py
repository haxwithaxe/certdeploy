"""Fixtures an utilities for testing client openrc-style serivce updating."""

from typing import Callable

import pytest
from fixtures.utils import Script


class RCServiceFlags:
    """Flag strings to write in the flag file."""

    FAILED = 'failed'
    INITIALIZED = 'initialized'
    RELOADED = 'reloaded'
    RESTARTED = 'restarted'


"""This script template has the following behaviors:
* Verifies that the appropriate service name is given.
    * Nothing is written to the flag file in the event the service name is
        correct.
    * The failure flag is written to the flag file if the name is invalid.
* Verifies that A valid action is given.
    * When the reload action is given the corresponding string is written to
        the flag file.
    * When the restart action is given the corresponding string is written to
        the flag file.
    * The failure flag is written to the flag file if the action is invalid.
"""
MOCK_RC_SERVICE_TEMPLATE = f'''\
#!/bin/bash

set -e

{{fail}}


# Verify the service name given is the right service name
if [[ "$1" != "{{service_name}}" ]]; then
    echo Invalid service name \\"$1\\"
    echo {RCServiceFlags.FAILED} > "{{flag_file_path}}"
    exit 1
fi


# Verify a valid action is given
case $2 in
    restart)
        echo {RCServiceFlags.RESTARTED} > "{{flag_file_path}}"
        ;;
    reload)
        echo {RCServiceFlags.RELOADED} > "{{flag_file_path}}"
        ;;
    *)
        echo Invalid action \\"$1\\"
        echo {RCServiceFlags.FAILED} > "{{flag_file_path}}"
        exit 2
        ;;
esac
'''


@pytest.fixture(scope='function')
def tmp_rc_service(
    tmp_script: Callable[[str, str, str, str], Script]
) -> Callable[[str, bool], tuple[str, Script]]:
    """Return a factory for temporary openrc-style `service`."""

    def _tmp_rc_service(
        service_name: str = 'certdeploy-test.rc_service', fail: bool = False
    ) -> tuple[str, Script]:
        """Return a unit name and mock rc `service`.

        Arguments:
            service_name: The desired unit name. Defaults to
                'certdeploy-test.rc_service'.
            fail: If `True` a command is inserted into the mock `service` that
                causes premature failure. Defaults to `False`

        Returns:
            A service name the mock rc `service` is expecting and the
            script object for the mock rc `service`.
        """
        fail_str = ''
        if fail:
            # The guaranteed fail mode command
            fail_str = (
                f'echo {RCServiceFlags.FAILED} > '
                '{flag_file_path}; exit 3'  # fmt: skip
            )
        # Create a mock `service` that will detect if the right args are
        #   passed.
        mock_rc_service = tmp_script(
            'mock-rc-service',
            MOCK_RC_SERVICE_TEMPLATE,
            service_name=service_name,
            fail=fail_str,
        )
        # The tests expects the file to exist so a neutral payload is written to
        #   it.
        mock_rc_service.flag_file.write_text(RCServiceFlags.INITIALIZED)
        return service_name, mock_rc_service

    return _tmp_rc_service
