"""Random small fixtures and utilities."""

import pathlib
import socket
import stat
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable

import pytest
from fixtures.keys import KeyPair

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
class ConfigContext:
    """A wrapper for important config generation related values."""

    config_path: pathlib.Path
    """The generated config path."""
    config: dict
    """The config used to generate the config file at `config_path`"""
    client_keypair: KeyPair = None
    """The optional client keypair."""
    server_keypair: KeyPair = None
    """The optional server keypair."""

    def __iter__(self):
        """Imitate the original tuple to reduce rewrites."""
        return iter((self.config_path, self.config))


class _Ports:
    """A registry of ports use in testing."""

    _claimed: list[int] = []
    """A list of claimed ports."""

    @classmethod
    def claim(cls, port: int) -> bool:
        """Attempt to claim a port.

        Arguments:
            port: The port number to be claimed.

        Returns:
            `True` if the port is not claimed already. `False` if it is
            claimed.
        """
        if port in cls._claimed:
            return False
        cls._claimed.append(port)
        return True


class KillSwitch(threading.Event):
    """A thread-safe boolean signal.

    Defaults to `False`.

    Attributes:
        id: A unique ID for each instance of `KillSwitch`. Just for debugging.

    Example:

        ...
        kill_switch = KillSwitch()
        client = DeployServer(my_client_config)
        client._stop_running = kill_switch
        managed_thread(
            client.serve_forever,
            kill_switch=kill_switch,
            teardown=kill_switch.teardown(client)
        )
        ...

    """

    def __init__(self):  # noqa: D107
        threading.Event.__init__(self)
        self.id = uuid.uuid4()

    def teardown(self, looper: Any) -> callable:
        """Return a function that sets the `looper` back to defaults."""
        def _teardown():
            self.clear()
            looper._stop_running = False
        return _teardown

    def __bool__(self):
        """Return `True` if the event is set."""
        return self.is_set()


@dataclass
class Script:
    """A wrapper for a temporary script and a flag file."""

    path: pathlib.Path
    """The path of the temporary script."""
    flag_file: pathlib.Path = None
    """The path of the flag file."""
    alt_flag_file: pathlib.Path = None
    """An alternate path of the flag file. For instance the path when mounted
    in a docker container."""

    @property
    def flag_text(self) -> str:
        """The text content of the flag file."""
        return self.flag_file.read_text().strip()


@pytest.fixture()
def tmp_script(tmp_path_factory: pytest.TempPathFactory
               ) -> Callable[[str, str, pathlib.Path, pathlib.Path, ...],
                             Script]:
    """Return a temporary executable script factory."""

    def _tmp_script(name: str, template: str, tmp_path: pathlib.Path = None,
                    alt_flag_file: pathlib.Path = None, **format_kwargs: Any
                    ) -> Script:
        """Return a temporary executable script.

        Arguments:
            name: The name of the script.
            template: A template string compatible with `str.format()`.
                The following keys are available to all templates:
                    * flag_file_path: This is the `flag_file_path` variable
                        unless the `alt_flag_file_path` is set then that
                        variable is used. This allows scripts mounted in docker
                        containers to have the right path to the flag file.
            tmp_path: The base path for the script and flag file. Defaults to a
                new temporary directory.
            alt_flag_file: An alternate path of the flag file. For instance the
                path when mounted in a docker container.

        Keyword Arguments:
            fail: A special case that is formatted with the `flag_file_path`
                and the `format_kwargs` before formatting `template`.
            format_kwargs: Key value pairs to apply when formatting `fail` and
                `template`.

        Returns:
            A script wrapper with the path to the script and the flag file.
        """
        tmp_path = tmp_path or tmp_path_factory.mktemp('tmp_script')
        flag_file_path = tmp_path.joinpath('flag')
        format_flag_file_path = (alt_flag_file or tmp_path).joinpath('flag')
        script_path = tmp_path.joinpath(name)
        if 'fail' in format_kwargs:
            format_kwargs['fail'] = format_kwargs['fail'].format(
                flag_file_path=format_flag_file_path,
                **format_kwargs
            )
        script_path.write_text(template.format(
            flag_file_path=format_flag_file_path,
            **format_kwargs
        ))
        script_path.chmod(
            stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH |  # a+r
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH |  # a+x
            stat.S_IWUSR  # Allow the teardown to remove the script
        )
        return Script(script_path, flag_file_path, format_flag_file_path)

    return _tmp_script


@pytest.fixture(scope='function')
def lineage_factory(tmp_path_factory: pytest.TempPathFactory
                    ) -> Callable[[str, list[str]], pathlib.Path]:
    """Return a temporary lineage factory."""

    def _gen_lineage(lineage: str, filenames: list[str] = None) -> pathlib.Path:
        """Generate a temporary lineage.

        Arguments:
            lineage: The lineage name. Not the full path.
            filenames: A list of filenames to create. Defaults to
                `['fullchain.pem', 'privkey.pem']`.

        Returns:
            The path to the lineage directory.
        """
        filenames = filenames or ['fullchain.pem', 'privkey.pem']
        cert_dir = tmp_path_factory.mktemp('tmp_lineage')
        lineage_dir = cert_dir.joinpath(lineage)
        lineage_dir.mkdir()
        for filename in filenames:
            pem_path = lineage_dir.joinpath(filename)
            pem_path.write_bytes(_MOCK_PEM)
        return lineage_dir

    return _gen_lineage


def get_free_port(min_port: int = 1025, max_port: int = 65535,
                  address: str = '127.0.0.1') -> int:
    """Return the first free port between `min_port` and `max_port`.

    The range between `min_port` and `max_port` is inclusive.

    Note:
        This uses a global registry of selected ports so the previously
        discovered free ports don't have to be in use when selecting another
        free port.

    Arguments:
        min_port: The lowest acceptable port. Defaults to 1025.
        max_port: The highest acceptable port. Defaults to 65535.
        address: The address to bind to. Defaults to `'127.0.0.1'`.

    Returns:
        A free port between `min_port` and `max_port` (inclusive).

    Raises:
       NoFreePort: When there are no unused ports in the given range.
    """
    for port in range(min_port, max_port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((address, port))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if _Ports.claim(port):
                # Only close the socket on a successful connection or at the
                #   end of the process.
                sock.close()
                return port
        except OSError:
            pass
        finally:
            sock.close()
    raise NoFeePort()


@pytest.fixture(scope='function')
def free_port() -> Callable[[int, int, str], int]:
    """Return a free port number factory."""
    return get_free_port


@pytest.fixture(scope='function')
def wait_for_condition() -> Callable[[Callable[[], bool], int], None]:
    """Return a utility that waits for a function to be `True`."""

    def _wait_for_condition(condition: Callable[[], bool], timeout: int = 60):
        """Wait for `condition` to be `True`.

        Arguments:
            condition: A `callable` that requires no arguments and returns
                `True` when its conditions are met.
            timeout: The number of seconds to wait before giving up on
                `condition`. Defaults to 60.

        Raises:
            TimeoutError: If it takes more than `timeout` seconds for
                `condition` to become `True`.
        """
        for _ in range(1, int(timeout / 0.1)):
            if condition():
                return
            time.sleep(0.1)
        raise TimeoutError()

    return _wait_for_condition
