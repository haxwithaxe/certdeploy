"""Verify that the client configs are validated."""

from typing import Callable

from fixtures.client_config import ConfigContext
from fixtures.keys import KeyPair

from certdeploy.client.config import ClientConfig
from certdeploy.client.config.client import SFTPDConfig


def test_config_base_kitchen_sink(
    tmp_client_config_file: Callable[[], ConfigContext],
):
    """Quickly verify the kitchen sink is validated.

    Verify all the things that need to be validated in
    `certdeploy.client.config.client.Config` pass valid values.
    """
    context = tmp_client_config_file(update_delay='10s', sftpd={})
    config = ClientConfig.load(context.config_path)
    assert config.destination == context.config['destination']
    assert config.source == context.config['source']
    assert config.sftpd == context.config['sftpd']
    assert config.systemd_exec == context.config['systemd_exec']
    assert config.systemd_timeout == context.config['systemd_timeout']
    assert config.docker_url == context.config['docker_url']
    assert config.update_services == context.config['update_services']
    assert config.update_delay == context.config['update_delay']
    assert config.sftpd_config == SFTPDConfig()
    assert config.update_delay_seconds == 10


def test_config_sftpd_kitchen_sink(
    tmp_client_config_file: Callable[[], ConfigContext],
    keypairgen: Callable[[], KeyPair],
):
    """Quickly verify the SFTPD kitchen sink is validated.

    Verify all the things that need to be validated in
    `certdeploy.client.config.client.SFTPDConfig` pass valid values.
    """
    server_keypair = keypairgen()
    client_keypair = keypairgen()
    context = tmp_client_config_file(
        client_keypair=client_keypair,
        server_keypair=server_keypair,
        sftpd=dict(
            listen_port=22222,
            listen_address='1.2.3.4',
            username='test_username',
            privkey_filename='/dev/null',
            # This will not automatically be set by the fixtures if
            #   `server_pubkey_filename` is set.
            server_pubkey=server_keypair.pubkey_text,
            server_pubkey_filename='/dev/null.pub',
            log_level='DEBUG',
            log_filename='/dev/stdout',
            socket_backlog=13,
        ),
    )
    config = ClientConfig.load(context.config_path)
    sftp = config.sftp_config
    ctx = context.config['sftpd']
    assert sftp.listen_port == ctx['listen_port']
    assert sftp.listen_address == ctx['listen_address']
    assert sftp.username == ctx['username']
    assert sftp.privkey_filename == ctx['privkey_filename']
    assert sftp.server_pubkey == ctx['server_pubkey']
    assert sftp.server_pubkey_filename == ctx['server_pubkey_filename']
    assert sftp.log_level == ctx['log_level']
    assert sftp.log_filename == ctx['log_filename']
    assert sftp.socket_backlog == ctx['socket_backlog']
