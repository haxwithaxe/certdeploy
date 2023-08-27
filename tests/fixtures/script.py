
import os
import pathlib
import stat

import pytest

SCRIPT_TEMPLATE = '''\
#!/bin/sh
touch {flag_file_path}
'''


@pytest.fixture(scope='function')
def tmp_script(tmp_path: pathlib.Path):
    """Return a script to run and a flag file path to check."""
    script_path = tmp_path.joinpath('test_script.sh')
    flag_file_path = tmp_path.joinpath('test_script_flag_file')
    assert not os.path.exists(flag_file_path)
    script_path.write_text(SCRIPT_TEMPLATE.format(
        flag_file_path=flag_file_path
    ))
    script_path.chmod(
        stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH |  # a+r
        stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH |  # a+x
        stat.S_IWUSR  # Allow the teardown to remove the script
    )
    return script_path, flag_file_path
