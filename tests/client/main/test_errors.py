
import pytest

from certdeploy.client import _main


def test_main_with_no_args_exits_non_zero():
    with pytest.raises(SystemExit) as err:
        _main.main()
    assert err.value.code in (1, 2)
