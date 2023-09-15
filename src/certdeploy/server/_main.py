
import sys

import typer

from .. import DEFAULT_SERVER_CONFIG, LogLevel
from . import log
from .config import ServerConfig
from .renew import renew_certs
from .server import Server

_app = typer.Typer()


def _run(config, daemon, renew, push, lineage, domains):
    if renew:
        # This is used in tests to indicate the renew process has begun.
        log.debug('Running renew')
        renew_certs(config)
    elif daemon and not push:
        # This is used in tests to indicate the daemon is being run.
        log.debug('Running daemon')
        Server(config).serve_forever()
    else:
        log.debug('Running manual push or hook')
        if (not lineage or not domains) and not push:
            log.error('Could not find lineage or domains. lineage: %s, '
                      'domains: %s', lineage, domains)
            sys.exit(1)
        server = Server(config)
        if domains and lineage:
            log.debug('Adding lineage to queue.')
            domains = domains.split()
            server.sync(lineage, domains)
        if push:
            log.debug('Running manual push without a running daemon')
            server.serve_forever(one_shot=True)


@_app.command()
def _typer_main(
    config: str = typer.Option(
        DEFAULT_SERVER_CONFIG,
        envvar='CERTDEPLOY_SERVER_CONFIG',
        help='The path to the CertDeploy server config.'
    ),
    lineage: str = typer.Option(
        None,
        envvar='RENEWED_LINEAGE',
        help='The path of a lineage (eg `/etc/letsencrypt/live/example.com`). '
             'This is mutually exclusive with `--daemon`.'
    ),
    domains: str = typer.Option(
        '',
        envvar='RENEWED_DOMAINS',
        help='A space separated list of domains as a single string '
             '(eg `"www.example.com example.com"`). This is mutually exclusive '
             'with `--daemon`.'
    ),
    daemon: bool = typer.Option(
        False,
        envvar='CERTDEPLOY_SERVER_DAEMON',
        help='Run the daemon. Without this option the server command will run '
             'once and exit.'
    ),
    renew: bool = typer.Option(
        False,
        envvar='CERTDEPLOY_SERVER_RENEW_ONLY',
        help='Run the cert renewal part of the daemon once and exit.'
    ),
    push: bool = typer.Option(
        False,
        envvar='CERTDEPOLY_SERVER_PUSH_ONLY',
        help='Run the daemon only until the queue is empty and all pushes '
             'have been processed. When used with `--linea  ge` and `--domains`'
             ' it populates the queue and then runs the daemon until the push '
             'is complete.'
    ),
    log_level: LogLevel = typer.Option(
        None,
        envvar='CERTDEPLOY_SERVER_LOG_LEVEL',
        help='The CertDeploy log level. Defaults to \'ERROR\'.'
    ),
    log_filename: str = typer.Option(
        None,
        envvar='CERTDEPLOY_SERVER_LOG_FILENAME',
        help='The path to the CertDeploy log file. Defaults to `/dev/stdout` '
             '(the python `logging` default).'
    ),
    sftp_log_level: LogLevel = typer.Option(
        None,
        envvar='CERTDEPOLY_SFTP_LOG_LEVEL',
        help='The SFTP client log level. Defaults to \'ERROR\' '
             '(the `paramiko` default).'
    ),
    sftp_log_filename: str = typer.Option(
        None,
        envvar='CERTDEPOLY_SFTP_LOG_FILENAME',
        help='The path to the SFTP client log file. Defaults to `/dev/stdout` '
             '(the `paramiko` default).'
    )
):
    # Just in case there is a config error
    log.setLevel(log_level or LogLevel.ERROR)
    try:
        conf = ServerConfig.load(
            config,
            override_log_filename=log_filename,
            override_log_level=log_level,
            override_sftp_log_filename=sftp_log_filename,
            override_sftp_log_level=sftp_log_level
        )
        log.setLevel(log_level or conf.log_level)
        _run(conf, daemon, renew, push, lineage, domains)
    except Exception as err:
        log.error(err, exc_info=err)
        sys.exit(1)


def main():
    """`certdeploy-server` script entrypoint."""
    _app()
