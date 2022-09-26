
from certdeploy.server.config import ServerConfig


def test_loads_valid_server(tmp_server_config: callable):
    config_filename, src_config = tmp_server_config()
    config = ServerConfig.load(config_filename)
    assert config.privkey_filename == src_config['privkey_filename']
    assert config.client_configs == src_config['client_configs']
    assert config.fail_fast == src_config['fail_fast']
    assert config.log_level == src_config['log_level']
    assert config.renew_every == src_config['renew_every']
    assert config.renew_unit == src_config['renew_unit']
    assert config.renew_at == src_config['renew_at']
    assert config.renew_exec == src_config['renew_exec']
    assert config.renew_args == src_config['renew_args']
    assert config.renew_timeout == src_config['renew_timeout']


def test_loads_valid_client(tmp_server_config: callable, pubkeygen: callable):
    config_filename, src_config = tmp_server_config(
        client_configs=[dict(
            address='1.2.3.4',
            domains=['test.example.com'],
            pubkey=pubkeygen(),
            port=42,
            username='test username',
            path='/test/client/source/dir',
            needs_chain=True,
            needs_fullchain=False,
            needs_privkey=False
        )]
    )
    config = ServerConfig.load(config_filename)
    client = config.clients[0]
    src_client = src_config['client_configs'][0]
    assert client.address == src_client['address']
    assert client.domains == src_client['domains']
    assert client.pubkey == src_client['pubkey']
    assert client.port == src_client['port']
    assert client.username == src_client['username']
    assert client.path == src_client['path']
    assert client.needs_chain == src_client['needs_chain']
    assert client.needs_fullchain == src_client['needs_fullchain']
    assert client.needs_privkey == src_client['needs_privkey']
