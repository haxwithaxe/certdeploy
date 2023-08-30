"""Mock certbot fixtures and utilities."""

import pathlib

import pytest

"""This script template is for testing how CertDeploy calls certbot.

If the right arguments are passed to the script it will touch the flag file.
"""
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
def mock_certbot(tmp_script: callable) -> callable:
    """Return a mock certbot script factory."""

    def _mock_certbot(renew_args: list[str] = None) -> pathlib.Path:
        """Return a mock certbot script.

        Arguments:
            renew_args: The arguments the script will expect to be passed.
                        Defaults to `['renew']`.

        Returns:
            pathlib.Path: The path to the mock certbot script.
        """
        # DEFAULT VALUE: certdeploy.server.config.server.Server.renew_args
        renew_args = renew_args if renew_args else ['renew']
        mock_certbot_script = tmp_script(
            'mock_certbot.sh',
            SCRIPT_TEMPLATE,
            required_args=' '.join(renew_args)
        )
        return mock_certbot_script

    return _mock_certbot