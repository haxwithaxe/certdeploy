"""Tests for the `SystemdService` `name` option."""

from certdeploy.client.config import ClientConfig


def test_accepts_valid_name_slice_service(tmp_client_config_file: callable):
    # Testing all the unusual characters in the slice name (after the @).
    # Testing the .service suffix
    name = 're-test@sD0:_\\,c.service'
    action = 'reload'
    context = tmp_client_config_file(
        # In the order Systemd lists them
        update_services=[
            dict(type='systemd', name=name,
                 action=action),
        ]
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].name == name
    assert config.services[0].action == action


def test_accepts_valid_name_socket(tmp_client_config_file: callable):
    # Testing all the unusual characters in the name.
    # Testing the .socket suffix
    name = 're-testD0:_\\,c.socket'
    action = 'reload'
    context = tmp_client_config_file(
        update_services=[
            dict(type='systemd', name=name,
                 action=action),
        ]
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].name == name
    assert config.services[0].action == action


def test_accepts_valid_name_device(tmp_client_config_file: callable):
    name = 're-test.device'
    action = 'reload'
    context = tmp_client_config_file(
        update_services=[
            dict(type='systemd', name=name,
                 action=action),
        ]
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].name == name
    assert config.services[0].action == action


def test_accepts_valid_name_mount(tmp_client_config_file: callable):
    name = 're-test.mount'
    action = 'reload'
    context = tmp_client_config_file(
        update_services=[
            dict(type='systemd', name=name,
                 action=action),
        ]
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].name == name
    assert config.services[0].action == action


def test_accepts_valid_name_automount(tmp_client_config_file: callable):
    name = 're-test.automount'
    action = 'reload'
    context = tmp_client_config_file(
        update_services=[
            dict(type='systemd', name=name,
                 action=action),
        ]
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].name == name
    assert config.services[0].action == action


def test_accepts_valid_name_swap(tmp_client_config_file: callable):
    name = 're-test.swap'
    action = 'reload'
    context = tmp_client_config_file(
        update_services=[
            dict(type='systemd', name=name,
                 action=action),
        ]
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].name == name
    assert config.services[0].action == action


def test_accepts_valid_name_target(tmp_client_config_file: callable):
    name = 're-test.target'
    action = 'reload'
    context = tmp_client_config_file(
        update_services=[
            dict(type='systemd', name=name,
                 action=action),
        ]
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].name == name
    assert config.services[0].action == action


def test_accepts_valid_name_path(tmp_client_config_file: callable):
    name = 're-test.path'
    action = 'reload'
    context = tmp_client_config_file(
        update_services=[
            dict(type='systemd', name=name,
                 action=action),
        ]
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].name == name
    assert config.services[0].action == action


def test_accepts_valid_name_timer(tmp_client_config_file: callable):
    name = 're-test.timer'
    action = 'reload'
    context = tmp_client_config_file(
        update_services=[
            dict(type='systemd', name=name,
                 action=action),
        ]
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].name == name
    assert config.services[0].action == action


def test_accepts_valid_name_slice(tmp_client_config_file: callable):
    name = 're-test.slice'
    action = 'reload'
    context = tmp_client_config_file(
        update_services=[
            dict(type='systemd', name=name,
                 action=action),
        ]
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].name == name
    assert config.services[0].action == action


def test_accepts_valid_name_scope(tmp_client_config_file: callable):
    name = 're-test.scope'
    action = 'reload'
    context = tmp_client_config_file(
        update_services=[
            dict(type='systemd', name=name,
                 action=action),
        ]
    )
    config = ClientConfig.load(context.config_path)
    assert config.services[0].name == name
    assert config.services[0].action == action
