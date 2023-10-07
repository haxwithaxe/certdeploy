import sys

import typer

from .. import DEFAULT_CLIENT_CONFIG, LogLevel
from ..errors import ConfigError
from . import log
from .config import ClientConfig
from .daemon import DeployServer
from .deploy import deploy
from .update import update_services

_app = typer.Typer()


def _run(config: ClientConfig, daemon: bool):
    """Run the CertDeploy client.

    Arguments:
        config: The CertDeploy client config.
        daemon: If `True` run the daemon. Otherwise just run the deploy
            function.
    """
    if daemon:
        log.debug('Running daemon')
        DeployServer(config).serve_forever()
    else:
        log.debug('Running one off deploy')
        if deploy(config):
            log.debug('Updating services')
            update_services(config)


@_app.command()
def _typer_main(
    config: str = typer.Option(
        DEFAULT_CLIENT_CONFIG,
        envvar='CERTDEPLOY_CLIENT_CONFIG',
        help='The path to the CertDeploy client config.',
    ),
    daemon: bool = typer.Option(
        False, envvar='CERTDEPLOY_CLIENT_DAEMON', help='Run the daemon.'
    ),
    log_level: LogLevel = typer.Option(
        None,
        envvar='CERTDEPLOY_CLIENT_LOG_LEVEL',
        help='The CertDeploy log level. Defaults to \'ERROR\'.',
    ),
    log_filename: str = typer.Option(
        None,
        envvar='CERTDEPLOY_CLIENT_LOG_FILENAME',
    ),
    sftp_log_level: LogLevel = typer.Option(
        None,
        envvar='CERTDEPOLY_CLIENT_SFTP_LOG_LEVEL',
        help='The log level for the embedded SFTP server. Defaults to '
        '\'ERROR\'.',  # fmt: skip
    ),
    sftp_log_filename: str = typer.Option(
        None,
        envvar='CERTDEPOLY_CLIENT_SFTP_LOG_FILENAME',
        help='The path to the log file for the embedded SFTP server (paramiko).'
        ' Defaults to the paramiko default.',
    ),
):
    # Just in case there is a config error set the log level right away.
    log.setLevel(log_level or LogLevel.ERROR)
    try:
        conf = ClientConfig.load(
            config,
            override_log_filename=log_filename,
            override_log_level=log_level,
            override_sftp_log_filename=sftp_log_filename,
            override_sftp_log_level=sftp_log_level,
        )
    except FileNotFoundError as err:
        log.error('Config file "%s" not found: %s', config, err, exc_info=err)
        sys.exit(1)
    except (ConfigError, OSError) as err:
        log.error(err, exc_info=err)
        sys.exit(1)
    log.setLevel(log_level or conf.log_level)
    try:
        _run(conf, daemon)
    except Exception as err:
        log.error(err, exc_info=err)
        sys.exit(1)


if __name__ == '__main__':
    _app()
