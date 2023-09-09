
from typing import Any, Optional


def is_int(value: Any, min_value: Optional[int] = None,
           max_value: Optional[int] = None) -> bool:
    """Verify `value` is an integer between `min_value` and `max_value`.

    The range is exclusive.

    If `min_value` is not set this is equivalent to: `value` is less than
    `max_value`.

    If `max_value` is not set this is equivalent to: `value` is greater than
    `min_value`.

    If neither `min_value` or `max_value` are set this is equivalent to:
    `value` is an integer.
    """
    if not isinstance(value, int):
        return False
    if min_value is not None and value < min_value:
        return False
    if max_value is not None and value > max_value:
        return False
    return True


def is_optional_int(value: Any, min_value: Optional[int] = None,
                    max_value: Optional[int] = None) -> bool:
    """Verify `value` is `None` or an integer between `min_value` and
    `max_value`.

    The range is exclusive.

    If `min_value` is not set this is equivalent to: `value` is less than
    `max_value`.

    If `max_value` is not set this is equivalent to: `value` is greater than
    `min_value`.

    If neither `min_value` or `max_value` are set this is equivalent to:
    `value` is an integer or `None`.
    """  # noqa: D205,D400
    if value is None:
        return True
    return is_int(value, min_value, max_value)


def is_float(value: Any, min_value: Optional[float] = None,
             max_value: Optional[float] = None) -> bool:
    """Verify `value` is a float or integer between `min_value` and `max_value`.

    The range is exclusive.

    If `min_value` is not set this is equivalent to: `value` is less than
    `max_value`.

    If `max_value` is not set this is equivalent to: `value` is greater than
    `min_value`.

    If neither `min_value` or `max_value` are set this is equivalent to:
    `value` is a float or integer.
    """
    if not isinstance(value, (float, int)):
        return False
    if min_value is not None and value < min_value:
        return False
    if max_value is not None and value > max_value:
        return False
    return True


def is_optional_float(value: Any, min_value: Optional[float] = None,
                      max_value: Optional[float] = None) -> bool:
    """Verify `value` is `None` or a float or integer between `min_value` and
    `max_value`.

    The range is exclusive.

    If `min_value` is not set this is equivalent to: `value` is less than
    `max_value`.

    If `max_value` is not set this is equivalent to: `value` is greater than
    `min_value`.

    If neither `min_value` or `max_value` are set this is equivalent to:
    `value` is a float, integer, or `None`.
    """  # noqa: D205,D400
    if value is None:
        return True
    return is_float(value, min_value, max_value)
