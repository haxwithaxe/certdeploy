
import pytest

from certdeploy.server import _main


def test_main_with_no_args_exits_non_zero():
    """Verify not providing arguments causes an error."""
    with pytest.raises(SystemExit) as err:
        _main.main()
    # 2 is there because it returns 2 when pytest isn't capturing console
    #   output. It theoretically can't return 2 but haxwithaxe doesn't care as
    #   long as it's an expected non-zero value.
    assert err.value.code in (1, 2)
