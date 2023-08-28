
from certdeploy.server.config import ServerConfig
from certdeploy.server.config.server import PushMode


def test_loads_valid_server(tmp_server_config_file: callable):
    config_filename, src_config = tmp_server_config_file()
    config = ServerConfig.load(config_filename)
    assert config.privkey_filename == src_config['privkey_filename']
    assert config.client_configs == src_config['client_configs']
    assert config.fail_fast == src_config['fail_fast']
    assert config.log_level == src_config['log_level']
    assert config.renew_every == src_config['renew_every']
    assert config.renew_unit == src_config['renew_unit'] + 's'
    assert config.renew_at == src_config['renew_at']
    assert config.renew_exec == src_config['renew_exec']
    assert config.renew_args == src_config['renew_args']
    assert config.renew_timeout == src_config['renew_timeout']
    assert config.push_mode == PushMode(src_config['push_mode'])
    assert config.push_interval == src_config['push_interval']
    assert config.push_retries == src_config['push_retries']
    assert config.push_retry_interval == src_config['push_retry_interval']
    assert config.join_timeout == src_config['join_timeout']
    assert config.queue_dir == src_config['queue_dir']


def test_loads_valid_server_push_mode_serial(tmp_server_config_file: callable):
    config_filename, _ = tmp_server_config_file(
        push_mode='serial'
    )
    config = ServerConfig.load(config_filename)
    assert config.push_mode == PushMode.SERIAL


def test_loads_valid_server_push_mode_parallel(
        tmp_server_config_file: callable
):
    config_filename, _ = tmp_server_config_file(
        push_mode='parallel'
    )
    config = ServerConfig.load(config_filename)
    assert config.push_mode == PushMode.PARALLEL


def test_loads_valid_server_push_interval_zero(
        tmp_server_config_file: callable
):
    config_filename, _ = tmp_server_config_file(
        push_interval=0
    )
    config = ServerConfig.load(config_filename)
    assert config.push_interval == 0


def test_loads_valid_server_push_retries_zero(tmp_server_config_file: callable):
    config_filename, _ = tmp_server_config_file(
        push_retries=0
    )
    config = ServerConfig.load(config_filename)
    assert config.push_retries == 0


def test_loads_valid_server_push_retry_interval_zero(
        tmp_server_config_file: callable
):
    config_filename, _ = tmp_server_config_file(
        push_retry_interval=0
    )
    config = ServerConfig.load(config_filename)
    assert config.push_retry_interval == 0


def test_loads_valid_server_join_timeout_none(tmp_server_config_file: callable):
    config_filename, _ = tmp_server_config_file(
        join_timeout=None
    )
    config = ServerConfig.load(config_filename)
    assert config.join_timeout is None


def test_loads_valid_server_join_timeout_int(tmp_server_config_file: callable):
    config_filename, _ = tmp_server_config_file(
        join_timeout=1
    )
    config = ServerConfig.load(config_filename)
    assert config.join_timeout == 1


def test_loads_valid_client(tmp_server_config_file: callable,
                            pubkeygen: callable):
    config_filename, src_config = tmp_server_config_file(
        client_configs=[dict(
            address='1.2.3.4',
            domains=['test.example.com'],
            pubkey=pubkeygen(),
            port=42,
            username='test username',
            path='/test/client/source/dir',
            needs_chain=True,
            needs_fullchain=False,
            needs_privkey=False,
            push_retries=11,
            push_retry_interval=33
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
    assert client.push_retries == src_client['push_retries']
    assert client.push_retry_interval == src_client['push_retry_interval']


def test_loads_valid_client_push_retries_none(tmp_server_config_file: callable,
                                              pubkeygen: callable):
    config_filename, _ = tmp_server_config_file(
        client_configs=[dict(
            address='1.2.3.4',
            domains=['test.example.com'],
            pubkey=pubkeygen(),
            push_retries=None
        )]
    )
    config = ServerConfig.load(config_filename)
    client = config.clients[0]
    assert client.push_retries is None


def test_loads_valid_client_push_retries_zero(tmp_server_config_file: callable,
                                              pubkeygen: callable):
    config_filename, _ = tmp_server_config_file(
        client_configs=[dict(
            address='1.2.3.4',
            domains=['test.example.com'],
            pubkey=pubkeygen(),
            push_retries=0
        )]
    )
    config = ServerConfig.load(config_filename)
    client = config.clients[0]
    assert client.push_retries == 0


def test_loads_valid_client_push_retry_interval_none(
        tmp_server_config_file: callable,
        pubkeygen: callable
):
    config_filename, _ = tmp_server_config_file(
        client_configs=[dict(
            address='1.2.3.4',
            domains=['test.example.com'],
            pubkey=pubkeygen(),
            push_retry_interval=None
        )]
    )
    config = ServerConfig.load(config_filename)
    client = config.clients[0]
    assert client.push_retry_interval is None


def test_loads_valid_client_push_retry_interval_zero(
        tmp_server_config_file: callable,
        pubkeygen: callable
):
    config_filename, _ = tmp_server_config_file(
        client_configs=[dict(
            address='1.2.3.4',
            domains=['test.example.com'],
            pubkey=pubkeygen(),
            push_retry_interval=0
        )]
    )
    config = ServerConfig.load(config_filename)
    client = config.clients[0]
    assert client.push_retry_interval == 0
