
import os

import pytest
import yaml


@pytest.fixture(scope='function')
def tmp_server_config(tmp_path_factory: pytest.TempPathFactory,
                      pubkeygen: callable) -> callable:
    base_dir = tmp_path_factory.mktemp('conf')
    server_key = os.path.join(base_dir, 'server_key')
    open(server_key, 'w').close()
    config_filename = os.path.join(base_dir, 'client.yml')
    # Non-default values for top level options
    config = dict(
        privkey_filename=server_key,
        client_configs=[dict(
            address='test_client_address',
            domains=['example.com'],
            pubkey=pubkeygen()
        )],
        fail_fast=False,
        log_level='DEBUG',
        renew_every=2,
        renew_unit='hour',
        renew_at=':00',
        renew_exec='test_certbot',
        renew_args=['test_renew'],
        renew_timeout=None,
        push_mode='parallel',
        push_interval=7,
        push_retries=11,
        push_retry_interval=41,
        join_timeout=371,
        # Has to be a real dir writable by the test user
        queue_dir='/tmp'
    )

    def set_config(**conf):
        config.update(conf)
        with open(config_filename, 'w') as config_file:
            yaml.safe_dump(config, config_file)
        return config_filename, config

    return set_config
