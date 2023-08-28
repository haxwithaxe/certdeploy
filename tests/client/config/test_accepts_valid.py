

from certdeploy.client.config import ClientConfig
from certdeploy.client.config.client import SFTPDConfig


def test_config_base_kitchen_sink(tmp_client_config_file: callable):
    # Setting update_delay here since we're checking update_delay_seconds
    config_filename, src_config = tmp_client_config_file(update_delay='10s')
    config = ClientConfig.load(config_filename)
    assert config.destination == src_config['destination']
    assert config.source == src_config['source']
    assert config.sftpd == src_config['sftpd']
    assert config.systemd_exec == src_config['systemd_exec']
    assert config.systemd_timeout == src_config['systemd_timeout']
    assert config.docker_url == src_config['docker_url']
    assert config.update_services == src_config['update_services']
    assert config.update_delay == src_config['update_delay']
    assert config.sftpd_config == SFTPDConfig()
    assert config.update_delay_seconds == 10


def test_config_sftpd_kitchen_sink(tmp_client_config_file: callable,
                                   pubkeygen: callable):
    config_filename, src_config = tmp_client_config_file(
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
    config = ClientConfig.load(config_filename)
    assert (config.sftpd_config.listen_port ==
            src_config['sftpd']['listen_port'])
    assert (config.sftpd_config.listen_address ==
            src_config['sftpd']['listen_address'])
    assert config.sftpd_config.username == src_config['sftpd']['username']
    assert (config.sftpd_config.privkey_filename ==
            src_config['sftpd']['privkey_filename'])
    assert (config.sftpd_config.server_pubkey ==
            src_config['sftpd']['server_pubkey'])
    assert (config.sftpd_config.server_pubkey_filename ==
            src_config['sftpd']['server_pubkey_filename'])
    assert config.sftpd_config.log_level == src_config['sftpd']['log_level']
    assert (config.sftpd_config.log_filename ==
            src_config['sftpd']['log_filename'])
    assert (config.sftpd_config.socket_backlog ==
            src_config['sftpd']['socket_backlog'])
