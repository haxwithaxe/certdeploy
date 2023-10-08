"""Tests to verify the behavior of the CertDeploy Server config."""

from typing import Callable

from fixtures.utils import ConfigContext

from certdeploy.server.config import ServerConfig
from certdeploy.server.config.server import PushMode


def test_loads_valid_server(
    tmp_server_config_file: Callable[[...], ConfigContext],
):
    """Test a bunch of stuff all at once."""
    context = tmp_server_config_file()
    config = ServerConfig.load(context.config_path)
    assert config.privkey_filename == context.config['privkey_filename']
    assert config.client_configs == context.config['client_configs']
    assert config.fail_fast == context.config['fail_fast']
    assert config.log_level == context.config['log_level']
    assert config.renew_every == context.config['renew_every']
    assert config.renew_unit == context.config['renew_unit'] + 's'
    assert config.renew_at == context.config['renew_at']
    assert config.renew_exec == context.config['renew_exec']
    assert config.renew_args == context.config['renew_args']
    assert config.renew_timeout == context.config['renew_timeout']
    assert config.push_mode == PushMode(context.config['push_mode'])
    assert config.push_interval == context.config['push_interval']
    assert config.push_retries == context.config['push_retries']
    assert config.push_retry_interval == context.config['push_retry_interval']
    assert config.join_timeout == context.config['join_timeout']
    assert config.queue_dir == context.config['queue_dir']
    assert config.sftp_log_filename == context.config['sftp_log_filename']
    assert config.sftp_log_level == context.config['sftp_log_level']


def test_loads_valid_server_push_mode_serial(
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify the `push_mode` ``serial`` is translated correctly."""
    context = tmp_server_config_file(push_mode='serial')
    config = ServerConfig.load(context.config_path)
    assert config.push_mode == PushMode.SERIAL


def test_loads_valid_server_push_mode_parallel(
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify the `push_mode` ``parallel`` is translated correctly."""
    context = tmp_server_config_file(push_mode='parallel')
    config = ServerConfig.load(context.config_path)
    assert config.push_mode == PushMode.PARALLEL


def test_loads_valid_server_push_interval_zero(
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify that a valid `push_interval` is accepted."""
    context = tmp_server_config_file(push_interval=0)
    config = ServerConfig.load(context.config_path)
    assert config.push_interval == 0


def test_loads_valid_server_push_retries_zero(
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify that a valid `push_retries` is accepted."""
    context = tmp_server_config_file(push_retries=0)
    config = ServerConfig.load(context.config_path)
    assert config.push_retries == 0


def test_loads_valid_server_push_retry_interval_zero(
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify that a valid `push_retry_interval` is accepted."""
    context = tmp_server_config_file(push_retry_interval=0)
    config = ServerConfig.load(context.config_path)
    assert config.push_retry_interval == 0


def test_loads_valid_server_join_timeout_none(
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify that a valid `join_timeout` (`None`) is accepted."""
    context = tmp_server_config_file(join_timeout=None)
    config = ServerConfig.load(context.config_path)
    assert config.join_timeout is None


def test_loads_valid_server_join_timeout_int(
    tmp_server_config_file: Callable[[...], ConfigContext]
):
    """Verify that a valid `join_timeout` (number) is accepted."""
    context = tmp_server_config_file(join_timeout=1)
    config = ServerConfig.load(context.config_path)
    assert config.join_timeout == 1


def test_loads_valid_client(
    pubkeygen: Callable[[], str],
    tmp_server_config_file: Callable[[...], ConfigContext],
):
    """Verify that a valid client config is populated correctly."""
    context = tmp_server_config_file(
        client_configs=[
            dict(
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
                push_retry_interval=33,
            )
        ]
    )
    config = ServerConfig.load(context.config_path)
    client = config.clients[0]
    src_client = context.config['client_configs'][0]
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


def test_loads_valid_client_push_retries_none(
    pubkeygen: Callable[[], str],
    tmp_server_config_file: Callable[[...], ConfigContext],
):
    """Verify that a valid client `push_retries` (`None`) is accepted."""
    context = tmp_server_config_file(
        client_configs=[
            dict(
                address='1.2.3.4',
                domains=['test.example.com'],
                pubkey=pubkeygen(),
                push_retries=None,
            )
        ]
    )
    config = ServerConfig.load(context.config_path)
    client = config.clients[0]
    assert client.push_retries is None


def test_loads_valid_client_push_retries_zero(
    pubkeygen: Callable[[], str],
    tmp_server_config_file: Callable[[...], ConfigContext],
):
    """Verify that a valid client `push_retries` (number) is accepted."""
    context = tmp_server_config_file(
        client_configs=[
            dict(
                address='1.2.3.4',
                domains=['test.example.com'],
                pubkey=pubkeygen(),
                push_retries=0,
            )
        ]
    )
    config = ServerConfig.load(context.config_path)
    client = config.clients[0]
    assert client.push_retries == 0


def test_loads_valid_client_push_retry_interval_none(
    pubkeygen: Callable[[], str],
    tmp_server_config_file: Callable[[...], ConfigContext],
):
    """Verify that a valid client `push_retry_interval` (`None`) is accepted."""
    context = tmp_server_config_file(
        client_configs=[
            dict(
                address='1.2.3.4',
                domains=['test.example.com'],
                pubkey=pubkeygen(),
                push_retry_interval=None,
            )
        ]
    )
    config = ServerConfig.load(context.config_path)
    client = config.clients[0]
    assert client.push_retry_interval is None


def test_loads_valid_client_push_retry_interval_zero(
    pubkeygen: Callable[[], str],
    tmp_server_config_file: Callable[[...], ConfigContext],
):
    """Verify that a valid client `push_retry_interval` (number) is accepted."""
    context = tmp_server_config_file(
        client_configs=[
            dict(
                address='1.2.3.4',
                domains=['test.example.com'],
                pubkey=pubkeygen(),
                push_retry_interval=0,
            )
        ]
    )
    config = ServerConfig.load(context.config_path)
    client = config.clients[0]
    assert client.push_retry_interval == 0
