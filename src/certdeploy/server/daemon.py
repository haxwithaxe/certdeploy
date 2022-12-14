
from .config import ServerConfig
from .server import Server


def serve_forever(config: ServerConfig):
    """FIXME

    Arguments:
        config (ServerConfig): `ServerConfig`

    """
    Server(config).serve_forever()
