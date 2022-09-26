
from certdeploy.client.config import ClientConfig
from certdeploy.client.config.service import SystemdUnit


def test_accepts_valid_action_reload(tmp_client_config: callable):
    name = 'action-test.service'
    action = 'reload'
    config_filename, src_config = tmp_client_config(
        update_services=[
            dict(type='systemd', name=name,
                 action=action),
        ]
    )
    config = ClientConfig.load(config_filename)
    assert config.services[0].name == name
    assert config.services[0].action == action


def test_accepts_valid_action_restart(tmp_client_config: callable):
    name = 'action-test.service'
    action = 'restart'
    config_filename, src_config = tmp_client_config(
        update_services=[
            dict(type='systemd', name=name,
                 action=action),
        ]
    )
    config = ClientConfig.load(config_filename)
    assert config.services[0].name == name
    assert config.services[0].action == action


def test_accepts_valid_action_none(tmp_client_config: callable):
    name = 'action-test.service'
    action = None
    config_filename, src_config = tmp_client_config(
        update_services=[
            dict(type='systemd', name=name,
                 action=action),
        ]
    )
    config = ClientConfig.load(config_filename)
    assert config.services[0].name == name
    assert config.services[0].action == SystemdUnit.action


def test_accepts_valid_action_empty(tmp_client_config: callable):
    name = 'action-test.service'
    action = ''
    config_filename, src_config = tmp_client_config(
        update_services=[
            dict(type='systemd', name=name,
                 action=action),
        ]
    )
    config = ClientConfig.load(config_filename)
    assert config.services[0].name == name
    assert config.services[0].action == SystemdUnit.action
