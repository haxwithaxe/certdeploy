"""
    Dummy conftest.py for certdeploy.

    If you don't know what this is for, just leave it empty.
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
    ContainerStatus,
    ContainerWrapper,
    canned_docker_container
)
from fixtures.keys import (  # noqa: F401
    keypairgen,
    keypairgen_privkey_file,
    pubkeygen
)
from fixtures.mock_certbot import mock_certbot  # noqa: F401
from fixtures.mock_fail_client import mock_fail_client  # noqa: F401
from fixtures.script import tmp_script_for_service  # noqa: F401
from fixtures.server_config import (  # noqa: F401
    client_conn_config_factory,
    tmp_server_config,
    tmp_server_config_file
)
from fixtures.systemd import SystemdFlags, tmp_systemd_service  # noqa: F401
from fixtures.utils import (  # noqa: F401
    Script,
    free_port,
    lineage_factory,
    tmp_script
)
