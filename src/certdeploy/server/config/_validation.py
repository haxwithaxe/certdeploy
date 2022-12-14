
from typing import Any, Optional


def is_int(value: Any, min_value: Optional[int] = None,
           max_value: Optional[int] = None) -> bool:
    if not isinstance(value, int):
        return False
    if min_value is not None and value < min_value:
        return False
    if max_value is not None and value > max_value:
        return False
    return True


def is_optional_int(value: Any, min_value: Optional[int] = None,
                    max_value: Optional[int] = None) -> bool:
    if value is None:
        return True
    return is_int(value, min_value, max_value)


def is_float(value: Any, min_value: Optional[float] = None,
             max_value: Optional[float] = None) -> bool:
    if not isinstance(value, (float, int)):
        return False
    if min_value is not None and value < min_value:
        return False
    if max_value is not None and value > max_value:
        return False
    return True


def is_optional_float(value: Any, min_value: Optional[float] = None,
                      max_value: Optional[float] = None) -> bool:
    if value is None:
        return True
    return is_float(value, min_value, max_value)
