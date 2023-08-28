
import enum
import pathlib
import stat

import pytest

SYSTEMD_USER_MODE = True
SYSTEMD_SUDO = False


class SystemdFlags(enum.Enum):
    """Flag strings to write in the flag file."""

    RELOADED = 'reloaded'
    RESTARTED = 'restarted'


MOCK_SYSTEMCTL_TEMPLATE = f'''\
#!/bin/bash

case $1 in
    restart)
        echo {SystemdFlags.RESTARTED.value} > "{{flag_file}}"
        ;;
    reload)
        echo {SystemdFlags.RELOADED.value} > "{{flag_file}}"
        ;;
    *)
        echo Invalid action $1
        exit 1
        ;;
esac

if [[ "$2" != "{{unit_name}}" ]]; then
    echo Invalid unit name $2
    exit 2
fi
'''


@pytest.fixture(scope='function')
def tmp_systemd_service(tmp_path_factory: pytest.TempPathFactory) -> callable:
    """Return a temporary Systemd service factory."""

    def _tmp_systemd_service(unit_name='certdeploy-test.service'
                             ) -> tuple[pathlib.Path, str]:
        """Start a temporary Systemd service."""
        tmp_path = tmp_path_factory.mktemp('update-systemd')
        # Create a flag file with contents that don't match any other possible
        #   values. The file will be read not just verified that it exists.
        flag_file_path = tmp_path.joinpath('test_flag')
        flag_file_path.write_text('initialized')
        # Create a mock systemctl that will detect if the right args are
        #   passed.
        mock_systemctl_path = tmp_path.joinpath('mock_systemctl')
        mock_systemctl_path.write_text(
            MOCK_SYSTEMCTL_TEMPLATE.format(
                flag_file=flag_file_path,
                unit_name=unit_name
            )
        )
        mock_systemctl_path.chmod(
            stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH |  # a+r
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH |  # a+x
            stat.S_IWUSR  # Allow the teardown to remove the script
        )
        return flag_file_path, unit_name, mock_systemctl_path

    yield _tmp_systemd_service
