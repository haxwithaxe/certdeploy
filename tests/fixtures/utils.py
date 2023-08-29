"""Random small fixtures."""
import pathlib
import socket
import stat
from dataclasses import dataclass

import pytest

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

    pass


@dataclass
class Script:

    path: pathlib.Path
    flag_file: pathlib.Path = None


@pytest.fixture()
def tmp_script(tmp_path_factory: pytest.TempPathFactory) -> callable:
    """Return an executable script."""

    def _script(name, template, **format_kwargs) -> Script:
        tmp_path = tmp_path_factory.mktemp('tmp_script')
        flag_file_path = tmp_path.joinpath('flag')
        script_path = tmp_path.joinpath(name)
        script_path.write_text(template.format(flag_file_path=flag_file_path,
                                               **format_kwargs))
        script_path.chmod(
            stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH |  # a+r
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH |  # a+x
            stat.S_IWUSR  # Allow the teardown to remove the script
        )
        return Script(script_path, flag_file_path)

    return _script


@pytest.fixture()
def lineage_factory(tmp_path_factory: pytest.TempPathFactory) -> callable:
    """Generate a temporary lineage."""

    def _gen_lineage(lineage: str, filenames: list[str]) -> pathlib.Path:
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
    """Returns the first free port between `min_port` and `max_port`
    The range between `min_port` and `max_port` is inclusive.

    Arguments:
        min_port: The lowest acceptable port. Defaults to 1025.
        max_port: The highest acceptable port. Defaults to 65535.
        address: The address to bind to. Defaults to "127.0.0.1".

    Returns:
        int: A free port.

    Raises:
       NoFreePort: when there are no unused ports in the given range.
    """

    def _get_free_port(min_port: int = 1025, max_port: int = 65535,
                       address: str = '127.0.0.1') -> int:
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

    return _get_free_port
