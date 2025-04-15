"""CertDeploy Client deploy code."""

import glob
import os
import re
import shutil
from typing import Union

from . import log
from .config import ClientConfig
from .errors import InvalidKey

# Match a valid privkey.pem
PRIVKEY_RE = re.compile(
    r'\s*-----BEGIN(?: .*)? PRIVATE KEY-----'
    r'(?:\n|\r|\r\n)(?:[0-9a-zA-Z\+\/=]{64}(?:\n|\r|\r\n))*'
    r'(?:[0-9a-zA-Z\+\/=]{1,63}(?:\n|\r|\r\n))?'
    r'-----END(?: .*)? PRIVATE KEY-----\s*',
    re.M,
)
# Match a valid fullchain.pem or chain.pem
FULLCHAIN_RE = re.compile(
    r'(\s*-----BEGIN CERTIFICATE-----'
    r'(\n|\r|\r\n)([0-9a-zA-Z\+\/=]{64}(\n|\r|\r\n))*'
    r'([0-9a-zA-Z\+\/=]{1,63}(\n|\r|\r\n))?'
    r'-----END CERTIFICATE-----\s*)+',
    re.M,
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


def needs_update(
    source_filename: os.PathLike,
    dest_filename: os.PathLike,
) -> bool:
    """Verify that `dest_filename` needs to be updated.

    Arguments:
        source_filename: The incoming cert file.
        dest_filename: The previously deployed cert file.

    Returns:
        bool: `True` if `dest_filename` does not exist or if `dest_filename`
              exists and is not the same as `source_filename`.
    """
    if os.path.exists(dest_filename):
        with open(source_filename, 'rb') as src_file:
            source_text = src_file.read()
        with open(dest_filename, 'rb') as dest_file:
            dest_text = dest_file.read()
        if source_text == dest_text:
            log.debug(
                '%s and %s have the same contents',
                source_filename,
                dest_filename,
            )
            return False
        return True
    return True


def _set_permissions(
    path: os.PathLike,
    mode: int,
    owner: Union[int, None, str],
    group: Union[int, None, str],
):
    log.debug(
        'Setting permissions: path=%s, mode=%s, owner=%s, group=%s',
        path,
        mode if mode is None else oct(mode),
        owner,
        group,
    )
    if mode is not None:
        os.chmod(path, mode)
    if owner is not None:
        shutil.chown(path, owner)
    if group is not None:
        shutil.chown(path, group=group)


def deploy(config: ClientConfig) -> bool:
    """Deploy the certificates.

    Returns `True` if new certificates were deployed.
    """
    log.debug('Deploying')
    update = False
    if not os.listdir(config.source):
        log.debug('Source directory is empty: %s', config.source)
        return False
    for lineage in os.listdir(config.source):
        log.debug('Found lineage: %s', lineage)
        if not os.path.isdir(os.path.join(config.source, lineage)):
            continue
        # Do not move invalid key files.
        validate_keys(config.source, lineage)
        # Move the lineages to the destination
        dest_dir = os.path.join(config.destination, lineage)
        os.makedirs(dest_dir, exist_ok=True)
        _set_permissions(
            dest_dir,
            config.permissions.directory_mode,
            config.permissions.owner,
            config.permissions.group,
        )
        pems_glob = os.path.join(config.source, lineage, '*.pem')
        for source_filename in glob.glob(pems_glob):
            log.debug('Found source file "%s"', source_filename)
            dest_filename = os.path.join(
                dest_dir,
                os.path.basename(source_filename),
            )
            if not needs_update(source_filename, dest_filename):
                log.debug(
                    'Not moving "%s" to "%s"',
                    source_filename,
                    dest_filename,
                )
                continue
            update = True
            shutil.move(source_filename, dest_filename)
            _set_permissions(
                dest_filename,
                config.permissions.mode,
                config.permissions.owner,
                config.permissions.group,
            )
            log.debug('Moved "%s" to "%s"', source_filename, dest_filename)
    return update
