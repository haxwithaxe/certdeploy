"""A mock CertDeploy client fixture.

This mock client is just a dumb TCP server to any calls to it should fail.
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
        self._log.append(datetime.datetime.now())

    def run(self):
        handler = _tcp_handler_factory(self._log_request)
        with socketserver.TCPServer((self.address, self.port),
                                    handler) as server:
            server.timeout = 1
            while self._keep_serving:
                server.handle_request()


@pytest.fixture()
def mock_fail_client(free_port: callable) -> callable:
    """A single mock CertDeploy client factory."""
    _port = free_port()
    server = MockClientTCPServer()

    def _serve(address: str, port: int = _port
               ) -> tuple[int, MockClientTCPServer]:
        server.address = address
        server.port = port
        server.start()
        return port, server

    yield _serve
    server.stop()
