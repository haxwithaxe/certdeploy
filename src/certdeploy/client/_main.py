
import sys

import typer

from .. import DEFAULT_CLIENT_CONFIG, LogLevel
from ..errors import ConfigError
from . import log
from .config import ClientConfig
from .daemon import DeployServer
from .deploy import deploy
from .update import update_services


def _run(config, daemon):
    if daemon:
        DeployServer(config).serve_forever()
    else:
        if deploy(config):
            update_services(config)


def _typer_main(
    config: str = typer.Option(DEFAULT_CLIENT_CONFIG,
                               envvar='CERTDEPLOY_CLIENT_CONFIG'),
    daemon: bool = typer.Option(False, envvar='CERTDEPLOY_CLIENT_DAEMON'),
    log_level: LogLevel = typer.Option(None, envvar='CERTDEPLOY_LOG_LEVEL'),
    log_file: str = typer.Option(None, envvar='CERTDEPLOY_LOG_FILE'),
    sftpd_log_level: LogLevel = typer.Option(None, envvar='SFTPD_LOG_LEVEL'),
    sftpd_log_file: str = typer.Option(None, envvar='SFTPD_LOG_FILE')
):
    # Just in case there is a config error
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
    """Function to run typer from `console_scripts`."""
    typer.run(_typer_main)


if __name__ == '__main__':
    main()
