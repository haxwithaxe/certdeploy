"""A mock CertDeploy client fixture.

This mock client is just a TCP server with some instrumentation. It should
cause any calls to it to fail on the server side.
"""

import datetime
import socketserver
import threading

import pytest


def _tcp_handler_factory(log_func: callable):

    class MockClientTCPHandler(socketserver.BaseRequestHandler):
        """TCP handler that runs a logging callback."""

        def handle(self):
            log_func()
            self.request.sendall(b'Mock fail client')

    return MockClientTCPHandler


class MockClientTCPServer(threading.Thread):
    """A mock CertDeploy client that cannot connect to the server."""

    def __init__(self):
        threading.Thread.__init__(self, daemon=True)
        self.address = None
        self.port = None
        self._keep_serving = True
        self._log = []

    @property
    def log(self):
        """The logs of the times the server was accessed.

        Also stops this mock client.
        """
        self.stop()
        return self._log

    def stop(self):
        """Stop the main loop and join the thread."""
        self._keep_serving = False
        self.join()

    def _log_request(self):
        """Log the current date and time."""
        self._log.append(datetime.datetime.now())

    def run(self):
        """Run the main loop."""
        handler = _tcp_handler_factory(self._log_request)
        with socketserver.TCPServer((self.address, self.port),
                                    handler) as server:
            server.timeout = 1
            while self._keep_serving:
                server.handle_request()


@pytest.fixture()
def mock_fail_client(free_port: callable) -> callable:
    """Return a mock CertDeploy client factory."""
    mock_clients = []

    def _mock_fail_client(address: str, port: int = None
                          ) -> MockClientTCPServer:
        client = MockClientTCPServer()
        mock_clients.append(client)
        client.address = address
        client.port = port or free_port()
        client.start()
        return client

    yield _mock_fail_client
    for client in mock_clients:
        client.stop()
