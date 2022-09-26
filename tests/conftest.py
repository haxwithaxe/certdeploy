"""
    Dummy conftest.py for certdeploy.

    If you don't know what this is for, just leave it empty.
    Read more about conftest.py under:
    - https://docs.pytest.org/en/stable/fixture.html
    - https://docs.pytest.org/en/stable/writing_plugins.html
"""


import pytest  # noqa: F401
from fixtures.client_config import tmp_client_config  # noqa: F401
from fixtures.keys import pubkeygen  # noqa: F401
from fixtures.server_config import tmp_server_config  # noqa: F401
