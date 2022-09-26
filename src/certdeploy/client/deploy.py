
import glob
import os
import re
import shutil

from . import log
from .config import Config
from .errors import InvalidKey

# Match a valid privkey.pem
PRIVKEY_RE = re.compile(
    r'-----BEGIN PRIVATE KEY-----'
    r'(\n|\r|\r\n)([0-9a-zA-Z\+\/=]{64}(\n|\r|\r\n))*'
    r'([0-9a-zA-Z\+\/=]{1,63}(\n|\r|\r\n))?'
    r'-----END PRIVATE KEY-----\n*',
    re.M
)
# Match a valid fullchain.pem or chain.pem
FULLCHAIN_RE = re.compile(
    r'(\s*-----BEGIN CERTIFICATE-----'
    r'(\n|\r|\r\n)([0-9a-zA-Z\+\/=]{64}(\n|\r|\r\n))*'
    r'([0-9a-zA-Z\+\/=]{1,63}(\n|\r|\r\n))?'
    r'-----END CERTIFICATE-----\s*)+',
    re.M
)
KEY_RE_SET = (PRIVKEY_RE, FULLCHAIN_RE)


def validate_keys(*path: os.PathLike):
    """Verify the keys are actually keys."""
    full_path = os.path.join(*path)
    for key_filename in glob.glob(os.path.join(full_path, '*.pem')):
        with open(key_filename, 'r', encoding='utf-8') as key_file:
            key_text = key_file.read()
        if not [True for r in KEY_RE_SET if r.match(key_text)]:
            raise InvalidKey(full_path)


def deploy(config: Config) -> bool:
    """Deploy the certificates.

    Returns `True` if new certificates were deployed.
    """
    update = False
    if not os.listdir(config.source):
        return False
    # Do not move invalid key files.
    for lineage in os.listdir(config.source):
        log.debug('Found lineage: %s', lineage)
        if not os.path.isdir(os.path.join(config.source, lineage)):
            continue
        validate_keys(config.source, lineage)
        # Move the lineages to the destination
        dest_dir = os.path.join(config.destination, lineage)
        os.makedirs(dest_dir, exist_ok=True)
        for cert in glob.glob(os.path.join(config.source, lineage, '*.pem')):
            update = True
            filename = os.path.join(dest_dir, os.path.basename(cert))
            shutil.move(cert, filename)
            log.debug('Moved "%s" to "%s"', cert, filename)
    return update
