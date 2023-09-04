"""Mock certbot fixtures and utilities."""

import os
import pathlib
from typing import Callable

import pytest
from fixtures.utils import Script

# This script template is for testing how CertDeploy calls certbot.
#   If the right arguments are passed to the script it will touch the flag file.
SCRIPT_TEMPLATE = '''\
#!/bin/sh

set -e

required_args={required_args}

if [ "$*" != "$required_args" ]; then
    echo failed
    exit 1
fi

echo passed
touch {flag_file_path}
'''


@pytest.fixture(scope='function')
def mock_certbot(tmp_script: Callable[[...], Script]
                 ) -> Callable[[list[str], pathlib.Path, os.PathLike], Script]:
    """Return a mock certbot script factory."""

    def _mock_certbot(renew_args: list[str] = None,
                      tmp_path: pathlib.Path = None,
                      alt_flag_file_path: os.PathLike = None) -> Script:
        """Return a mock certbot script.

        Arguments:
            renew_args: The arguments the script will expect to be passed.
                Defaults to `['renew']`.
            tmp_path: The base path for the script and flag file.
            alt_flag_file_path: An alternate path for the flag file. For
                instance a path to the file when mounted in a docker container.

        Returns:
            A mock certbot script.
        """
        # DEFAULT VALUE: certdeploy.server.config.server.Server.renew_args
        renew_args = renew_args if renew_args else ['renew']
        mock_certbot_script = tmp_script(
            'mock_certbot.sh',
            SCRIPT_TEMPLATE,
            tmp_path=tmp_path,
            alt_flag_file_path=alt_flag_file_path,
            required_args=' '.join(renew_args),
        )
        return mock_certbot_script

    return _mock_certbot
