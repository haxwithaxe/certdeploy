"""A mock CertDeploy client fixture.

This mock client is just a TCP server with some instrumentation. It should
cause any calls to it to fail on the server side.
"""

import socketserver
import threading
from datetime import datetime
from typing import Callable

import pytest


def _tcp_handler_factory(log_func: callable) -> socketserver.BaseRequestHandler:
    """Return a request handler with `log_func` embedded in its `handle`.

    Arguments:
        log_func: A function that does something the code it comes from cares
            about.
    Returns:
        A subclass of `MockClientTCPHandler` with a `handle` method that calls
        `log_func`.
    """

    class MockClientTCPHandler(socketserver.BaseRequestHandler):
        """TCP handler that runs a logging callback."""

        def handle(self):
            """Handle a request.

            Run the logging callback and send some output to make sure the
            other end is unhappy with what it sees.
            """
            log_func()
            # Reply with something that definitely isn't a SSH or SFTP
            #   handshake.
            self.request.sendall(b'Mock fail client')

    return MockClientTCPHandler


class MockClientTCPServer(threading.Thread):
    """A mock CertDeploy client that cannot connect to the server."""

    def __init__(self):
        """Override `threading.Thread.__init__`."""
        threading.Thread.__init__(self, daemon=True)
        self.address = None
        self.port = None
        self._keep_serving = True
        self._log = []

    @property
    def log(self) -> list[datetime]:
        """The logs of the times the server was accessed.

        Also stops this mock client.

        Returns:
            The access logs of the TCP server.
        """
        self.stop()
        return self._log

    def stop(self):
        """Stop the main loop and join the thread."""
        self._keep_serving = False
        self.join()

    def _log_request(self):
        """Log the current date and time.

        This is passed to the `_tcp_handler_factory` as the value of
        `log_func`.
        """
        self._log.append(datetime.now())

    def run(self):
        """Run the main loop.

        As long as `self._keep_serving` is `True` keep handling requests one at
        a time.
        """
        handler = _tcp_handler_factory(self._log_request)
        with socketserver.TCPServer((self.address, self.port),
                                    handler) as server:
            server.timeout = 1
            while self._keep_serving:
                server.handle_request()


@pytest.fixture()
def mock_fail_client(free_port: callable
                     ) -> Callable[[str, int], MockClientTCPServer]:
    """Return a mock CertDeploy client factory."""
    mock_clients = []

    def _mock_fail_client(address: str, port: int = None
                          ) -> MockClientTCPServer:
        """Return a started mock client server.

        Arguments:
            address: The listen address.
            port: The listen port. Defaults to a random free port.

        Returns:
            A naive mock CertDeploy client for server tests to fail to connect
            to.
        """
        client = MockClientTCPServer()
        mock_clients.append(client)
        client.address = address
        client.port = port or free_port()
        client.start()
        return client

    yield _mock_fail_client
    for client in mock_clients:
        client.stop()
