"""conftest.py for certdeploy.

Read more about conftest.py under:
- https://docs.pytest.org/en/stable/fixture.html
- https://docs.pytest.org/en/stable/writing_plugins.html
"""


import pytest  # noqa: F401
from fixtures.client_config import (  # noqa: F401
    tmp_client_config,
    tmp_client_config_file
)
from fixtures.docker_container import (  # noqa: F401
    canned_docker_container,
    client_docker_container,
    server_docker_container
)
from fixtures.docker_service import canned_docker_service  # noqa: F401
from fixtures.errors import (  # noqa: F401
    client_errors,
    format_invalid_value,
    format_invalid_value_must,
    server_errors
)
from fixtures.keys import keypairgen, pubkeygen  # noqa: F401
from fixtures.logging import log_file  # noqa: F401
from fixtures.mock_certbot import mock_certbot  # noqa: F401
from fixtures.mock_fail_client import mock_fail_client  # noqa: F401
from fixtures.mock_server import mock_server_push  # noqa: F401
from fixtures.script import tmp_script_for_service  # noqa: F401
from fixtures.server_config import (  # noqa: F401
    client_conn_config_factory,
    server_config_file,
    tmp_server_config,
    tmp_server_config_file
)
from fixtures.systemd import tmp_systemd_service  # noqa: F401
from fixtures.threading import managed_thread, simple_thread  # noqa: F401
from fixtures.utils import (  # noqa: F401
    free_port,
    lineage_factory,
    tmp_script,
    wait_for_condition
)
