"""A temporary script fixture for testing client script updating."""

from typing import Callable

import pytest
from fixtures.utils import Script

SCRIPT_TEMPLATE = '''\
#!/bin/sh
touch {flag_file_path}
'''


@pytest.fixture(scope='function')
def tmp_script_for_service(
    tmp_script: Callable[[str, str, ...], Script],
) -> Script:
    """Return a script to run and a flag file path to check.

    Returns:
        A temporary script file and flag file in a wrapper.
    """
    return tmp_script('script-for-service.sh', SCRIPT_TEMPLATE)
