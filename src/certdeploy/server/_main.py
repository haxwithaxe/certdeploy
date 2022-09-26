
import sys

import typer

from .. import DEFAULT_SERVER_CONFIG, LogLevel
from . import daemon as Daemon
from . import log
from .config import ServerConfig
from .renew import renew_certs
from .server import Server


def _run(config, daemon, renew, lineage, domains):
    if renew:
        log.debug('Running renew')
        renew_certs(config)
    elif daemon:
        log.debug('Running daemon')
        Daemon.serve_forever(config)
    else:
        log.debug('Running manual push or hook')
        if not lineage or not domains:
            print('Could not find lineage or domains.',
                  f'lineage: {lineage}, domains: {domains}', file=sys.stderr)
            sys.exit(1)
        domains = domains.split()
        Server(config).sync(lineage, domains)


def _typer_main(  # pylint: disable=too-many-arguments
        config: str = typer.Option(DEFAULT_SERVER_CONFIG,
                                   envvar='CERTDEPLOY_SERVER_CONFIG'),
        lineage: str = typer.Option(None, envvar='RENEWED_LINEAGE'),
        domains: str = typer.Option('', envvar='RENEWED_DOMAINS'),
        daemon: bool = typer.Option(False, envvar='CERTDEPLOY_SERVER_DAEMON'),
        renew: bool = typer.Option(False, envvar='CERTDEPLOY_RENEW_ONLY'),
        log_level: LogLevel = typer.Option(None, envvar='CERTDEPLOY_LOG_LEVEL')
):
    try:
        conf = ServerConfig.load(config)
        log.setLevel(log_level or conf.log_level)
        _run(conf, daemon, renew, lineage, domains)
    except Exception as err:  # pylint: disable=broad-except
        log.error(err, exc_info=err)
        sys.exit(1)


def main():
    """`certdeploy-server` script entrypoint."""
    typer.run(_typer_main)
