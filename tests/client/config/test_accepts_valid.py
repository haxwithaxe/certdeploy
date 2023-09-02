

from certdeploy.client.config import ClientConfig
from certdeploy.client.config.client import SFTPDConfig


def test_config_base_kitchen_sink(tmp_client_config_file: callable):
    # Setting update_delay here since we're checking update_delay_seconds
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


def test_config_sftpd_kitchen_sink(tmp_client_config_file: callable,
                                   pubkeygen: callable):
    context = tmp_client_config_file(
        sftpd=dict(
            listen_port=22222,
            listen_address='1.2.3.4',
            username='test_username',
            privkey_filename='/dev/null',
            server_pubkey=pubkeygen(),
            server_pubkey_filename='/dev/null.pub',
            log_level='DEBUG',
            log_filename='/dev/stdout',
            socket_backlog=13
        )
    )
    config = ClientConfig.load(context.config_path)
    assert (config.sftpd_config.listen_port ==
            context.config['sftpd']['listen_port'])
    assert (config.sftpd_config.listen_address ==
            context.config['sftpd']['listen_address'])
    assert config.sftpd_config.username == context.config['sftpd']['username']
    assert (config.sftpd_config.privkey_filename ==
            context.config['sftpd']['privkey_filename'])
    assert (config.sftpd_config.server_pubkey ==
            context.config['sftpd']['server_pubkey'])
    assert (config.sftpd_config.server_pubkey_filename ==
            context.config['sftpd']['server_pubkey_filename'])
    assert config.sftpd_config.log_level == context.config['sftpd']['log_level']
    assert (config.sftpd_config.log_filename ==
            context.config['sftpd']['log_filename'])
    assert (config.sftpd_config.socket_backlog ==
            context.config['sftpd']['socket_backlog'])
