"""A temporary script for testing client script updating."""

import pytest
from fixtures.utils import Script

SCRIPT_TEMPLATE = '''\
#!/bin/sh
touch {flag_file_path}
'''


@pytest.fixture(scope='function')
def tmp_script_for_service(tmp_script: callable) -> Script:
    """Return a script to run and a flag file path to check.

    Returns:
        Script: A temporary script file and flag file in a wrapper.
    """
    return tmp_script('script-for-service.sh', SCRIPT_TEMPLATE)
