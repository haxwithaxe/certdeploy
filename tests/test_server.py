
import pytest

from certdeploy.server import _main


def test_main_with_no_args_exits_non_zero():
    with pytest.raises(SystemExit) as err:
        _main.main()
    assert err.value.code == 1
