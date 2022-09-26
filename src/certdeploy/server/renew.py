
import subprocess

from ..errors import CertDeployError
from . import log
from .config import ServerConfig


def renew_certs(config: ServerConfig):
    """Run the command to renew certificates."""
    cmd = [config.renew_exec]
    cmd.extend(config.renew_args)
    log.debug('Checking for renewable certificates. Using command: %s', cmd)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    proc.wait(timeout=config.renew_timeout)
    log.info('Checked for renewable certificates.')
    log.debug(f'Ran `{" ".join(cmd)}` returned {proc.returncode} and '
              f'produced combined stdout/stderr: '
              f'{proc.stdout.read().decode()}')
    if proc.returncode != 0:
        if config.fail_fast:
            raise CertDeployError(f'Failed to run `{" ".join(cmd)}`')
        log.error(
            'Failed to renew or check for renewable certificates. '
            f'`{" ".join(cmd)}` returned {proc.returncode} and produced '
            f'combined stdout/stderr: {proc.stdout.read().decode()}'
        )
