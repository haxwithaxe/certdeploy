"""Verify the behavior of the command line options."""

import pathlib
from typing import Callable

from fixtures.logging import ServerRefLogMessages as RefMsgs
from fixtures.utils import ConfigContext
from typer.testing import CliRunner

from certdeploy.server._main import _app


def test_as_hook(
    log_file: pathlib.Path,
    tmp_server_config_file: Callable[[...], ConfigContext],
):
    """Verify that the server runs as a hook.

    The server must run as a certbot deploy hook when given only a lineage and
    domain.

    This also covers the `--config` option loading the given config file.
    """
    # String taken from certdeploy.server._main
    context = tmp_server_config_file(
        fail_fast=True, log_level='DEBUG', log_filename=str(log_file)
    )
    ## Run the test
    results = CliRunner(mix_stderr=True).invoke(
        _app,
        args=['--config', context.config_path],
        env={
            'RENEWED_LINEAGE': 'test.example.com',
            'RENEWED_DOMAINS': 'test.example.com',
        },
    )
    ## Verify the results
    assert results.exception is None
    assert RefMsgs.ADD_TO_QUEUE_MESSAGE.log in log_file.read_bytes()
