
import pathlib

import pytest

SCRIPT_TEMPLATE = '''\
#!/bin/sh

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
    """Return a mock certbot script."""

    def _mock_certbot(renew_args: list[str] = None) -> pathlib.Path:
        # DEFAULT VALUE: certdeploy.server.config.server.Server.renew_args
        renew_args = renew_args if renew_args else ['renew']
        mock_certbot_script = tmp_script(
            'mock_certbot.sh',
            SCRIPT_TEMPLATE,
            required_args=' '.join(renew_args)
        )
        return mock_certbot_script

    return _mock_certbot
