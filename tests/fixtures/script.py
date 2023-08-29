
from typing import Any

import pytest

SCRIPT_TEMPLATE = '''\
#!/bin/sh
touch {flag_file_path}
'''


@pytest.fixture(scope='function')
def tmp_script_for_service(tmp_script: callable) -> Any:
    """Return a script to run and a flag file path to check."""
    return tmp_script('script-for-service.sh', SCRIPT_TEMPLATE)
