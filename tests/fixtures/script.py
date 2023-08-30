"""A temporary script for testing client script updating."""

from typing import Any

import pytest

SCRIPT_TEMPLATE = '''\
#!/bin/sh
touch {flag_file_path}
'''


@pytest.fixture(scope='function')
def tmp_script_for_service(tmp_script: callable) -> Any:
    """Return a script to run and a flag file path to check.

    Returns:
        fixtures.utils.Script: A temporary script file and flag file in an
            object.
    """
    return tmp_script('script-for-service.sh', SCRIPT_TEMPLATE)
