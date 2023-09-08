
import sys

import typer

from .. import DEFAULT_CLIENT_CONFIG, LogLevel
from ..errors import ConfigError
from . import log
from .config import ClientConfig
from .daemon import DeployServer
from .deploy import deploy
from .update import update_services


def _run(config: ClientConfig, daemon: bool):
    """Run the CertDeploy client.

    Arguments:
        config: The CertDeploy client config.
        daemon: If `True` run the daemon. Otherwise just run the deploy
            function.
    """
    if daemon:
        DeployServer(config).serve_forever()
    else:
        if deploy(config):
            update_services(config)


def _typer_main(
    config: str = typer.Option(
        DEFAULT_CLIENT_CONFIG,
        envvar='CERTDEPLOY_CLIENT_CONFIG',
        help='The path to the CertDeploy client config.'
    ),
    daemon: bool = typer.Option(
        False,
        envvar='CERTDEPLOY_CLIENT_DAEMON',
        help='Run the daemon.'
    ),
    log_level: LogLevel = typer.Option(
        None,
        envvar='CERTDEPLOY_CLIENT_LOG_LEVEL',
        help='The CertDeploy log level. Defaults to \'ERROR\'.'
    ),
    log_file: str = typer.Option(None, envvar='CERTDEPLOY_CLIENT_LOG_FILE'),
    sftpd_log_level: LogLevel = typer.Option(
        None,
        envvar='CERTDEPOLY_CLIENT_SFTP_LOG_LEVEL',
        help='The log level for the embedded SFTP server. Defaults to '
             '\'ERROR\'.'
    ),
    sftpd_log_file: str = typer.Option(
        None,
        envvar='CERTDEPOLY_CLIENT_SFTP_LOG_FILE',
        help='The path to the log file for the embedded SFTP server (paramiko).'
             ' Defaults to the paramiko default.'
    )
):
    """The entry point for the CertDeploy client command line.

    Arguments:
        config: The path to the CertDeploy client config. Defaults to
            `DEFAULT_CLIENT_CONFIG`.
        daemon: If `True` run the daemon. Otherwise just run the deploy process
            once. Defaults to `False`.
        log_level: The CertDeploy log level. Defaults to `ERROR`.
        log_file: The CertDeploy log filename. Defaults to stdout (`logging`
            default).
        sftpd_log_level: The log level for the embedded SFTP server. Defaults to
            'ERROR'.
        sftpd_log_file: The path to the log file for the embedded SFTP server.
            Defaults to the `paramiko` default.
    """  # noqa: D401
    # Just in case there is a config error set the log level right away.
    log.setLevel(log_level or LogLevel.ERROR)
    try:
        conf = ClientConfig.load(
            config,
            override_log_file=log_file,
            override_log_level=log_level,
            override_sftpd_log_file=sftpd_log_file,
            override_sftpd_log_level=sftpd_log_level
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
    except Exception as err:  # pylint: disable=broad-except
        log.error(err, exc_info=err)
        sys.exit(1)


def main():
    """The function to run `typer` from `console_scripts`."""  # noqa: D401
    typer.run(_typer_main)


if __name__ == '__main__':
    main()
