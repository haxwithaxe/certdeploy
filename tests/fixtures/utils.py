"""Random small fixtures."""

import pathlib
import socket
import stat
from dataclasses import dataclass
from typing import Any

import pytest

# Just enough like a real PEM file to pass the tests used by the CertDeploy
#   client.
_MOCK_PEM = b'''\
-----BEGIN CERTIFICATE-----
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000
-----END CERTIFICATE-----'''


class NoFeePort(Exception):
    """A descriptive exception for when no free port is found."""


@dataclass
class Script:
    """A wrapper for a temporary script and a flag file."""

    path: pathlib.Path
    """The path of the temporary script."""
    flag_file: pathlib.Path = None
    """The path of the flag file."""

    @property
    def flag_text(self) -> str:
        """The text content of the flag file."""
        return self.flag_file.read_text().strip()


@pytest.fixture()
def tmp_script(tmp_path_factory: pytest.TempPathFactory) -> callable:
    """Return a temporary executable script factory."""

    def _tmp_script(name: str, template: str, **format_kwargs: Any) -> Script:
        """Return a temporary executable script.

        Arguments:
            name (str): The name of the script.
            template (str): A template string compatible with `str.format()`

        Keyword Arguments:
            fail (str, optional): A special case that is formatted with the
                `flag_file_path` and the `format_kwargs` before formatting
                `template`.
            format_kwargs (dict[str, str], optional): Key value pairs to apply
                when formatting `fail` and `template`.

        Returns:
            Script: A script wrapper with the path to the script and the flag
                file.
        """
        tmp_path = tmp_path_factory.mktemp('tmp_script')
        flag_file_path = tmp_path.joinpath('flag')
        script_path = tmp_path.joinpath(name)
        if 'fail' in format_kwargs:
            format_kwargs['fail'] = format_kwargs['fail'].format(
                flag_file_path=flag_file_path,
                **format_kwargs
            )
        script_path.write_text(template.format(flag_file_path=flag_file_path,
                                               **format_kwargs))
        script_path.chmod(
            stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH |  # a+r
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH |  # a+x
            stat.S_IWUSR  # Allow the teardown to remove the script
        )
        return Script(script_path, flag_file_path)

    return _tmp_script


@pytest.fixture()
def lineage_factory(tmp_path_factory: pytest.TempPathFactory) -> callable:
    """Return a temporary lineage factory."""

    def _gen_lineage(lineage: str, filenames: list[str] = None) -> pathlib.Path:
        """Generate a temporary lineage.

        Arguments:
            lineage (str): The lineage name. Not the full path.
            filenames (list[str], optional): A list of filenames to create.
                Defaults to `['fullchain.pem', 'privkey.pem']`.

        Returns:
            pathlib.Path: The path to the lineage directory.
        """
        if not filenames:
            filenames = ['fullchain.pem', 'privkey.pem']
        cert_dir = tmp_path_factory.mktemp('tmp_lineage')
        lineage_dir = cert_dir.joinpath(lineage)
        lineage_dir.mkdir()
        for filename in filenames:
            pem_path = lineage_dir.joinpath(filename)
            pem_path.write_bytes(_MOCK_PEM)
        return lineage_dir

    return _gen_lineage


@pytest.fixture()
def free_port() -> callable:
    """Returns a free port number factory."""

    def _free_port(min_port: int = 1025, max_port: int = 65535,
                   address: str = '127.0.0.1') -> int:
        """Returns the first free port between `min_port` and `max_port`.

        The range between `min_port` and `max_port` is inclusive.

        Arguments:
            min_port (int, optional): The lowest acceptable port. Defaults to
                1025.
            max_port (int, optional): The highest acceptable port. Defaults to
                65535.
            address (str, optional): The address to bind to. Defaults to
                "127.0.0.1".

        Returns:
            int: A free port between `min_port` and `max_port` (inclusive).

        Raises:
           NoFreePort: When there are no unused ports in the given range.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = min_port
        while min_port <= port <= max_port:
            try:
                sock.bind((address, port))
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.close()
                return port
            except OSError:
                port += 1
        raise NoFeePort()

    return _free_port
