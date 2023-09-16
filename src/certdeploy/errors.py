"""Exceptions to use with both CertDeploy servers and CertDeploy clients."""

from typing import Any


def _double_quote(value: str) -> str:
    """Return a string with added surrounding double quotes."""
    return f'"{value}"'


class CertDeployError(Exception):
    """CertDeploy specific error."""


class ConfigError(CertDeployError):
    """Configuration error."""


class ConfigInvalid(ConfigError):
    """Invalid configuration exception.

    Arguments:
        key: The config key.
        value: The value given in the config.
        must: If the value must have been something set this to be that
            thing. Defaults to `None`.
        config_desc: The description of the config if needed. Defaults to
            an empty string.

    Example:
        An example of formatting using `must`.

            ConfigInvalid(
                'renew_unit',
                None,
                must='not be a weekday if `renew_every` is set and not'
                     ' 1'
            ) -> ('Invalid value "None" for `renew_unit`. `renew_unit` '
                  'must not be a weekday if `renew_every` is set and '
                  'not 1.')


    """

    def __init__(self, key: str, value: Any, must: str = None,  # noqa: D107
                 config_desc: str = ''):
        # Add a space to the description if it is set
        if config_desc:
            config_desc = f'{config_desc} '
        if must:
            super().__init__(f'Invalid value "{value}" for {config_desc}'
                             f'`{key}`. `{key}` must {must}.')
        else:
            super().__init__(f'Invalid value "{value}" for {config_desc}'
                             f'`{key}`.')


class ConfigInvalidNumber(ConfigInvalid):
    """Invalid numeric configuration exception.

    Arguments:
        key: The config key.
        value: The value given in the config.
        is_type: The name of the required number type. Defaults to
            `'number'`.
        optional: If `True` `'if set'` is added to the end of the message.
            Defaults to `False`.
        gt: Changes the phrasing to reflect the config must be
            'greater than' the value of `gt`. Defaults to `None`.
        lt: Changes the phrasing to reflect the config must be 'less than'
            the value of `lt`. Defaults to `None`.
        ge: Changes the phrasing to reflect the config must be 'greater than
            or equal to' the value of `ge`. Defaults to `None`.
        le: Changes the phrasing to reflect the config must be 'less than or
            equal to' the value of `le`. Defaults to `None`.
        config_desc: The description of the config if needed. Defaults to
            an empty string.
    """

    def __init__(self, key: str, value: Any, is_type: str = 'number',  # noqa: D107,E501
                 optional: bool = False, gt: str = None, lt: str = None,
                 ge: str = None, le: str = None, config_desc: str = ''):
        if is_type == int:
            is_type = 'integer'
        elif is_type == float:
            is_type = 'float'
        if not isinstance(is_type, str):
            is_type = str(is_type)
        bounds = []
        bounds_str = ''
        if gt is not None:
            bounds.append(f'greater than {gt}')
        if lt is not None:
            bounds.append(f'less than {lt}')
        if ge is not None:
            bounds.append(f'greater than or equal to {ge}')
        if le is not None:
            bounds.append(f'less than or equal to {le}')
        if bounds:
            bounds_str = f' {" and ".join(bounds)}'
        if_set = ''
        if optional:
            if_set = ' if set'
        a_or_an = 'a'
        if is_type[0] in ('a', 'e', 'i', 'o', 'u'):
            a_or_an = 'an'
        super().__init__(key, value, must=f'be {a_or_an} {is_type}{bounds_str}'
                         f'{if_set}', config_desc=config_desc)


class ConfigInvalidChoice(ConfigInvalid):
    """Invalid configuration from selection.

    Note:
        `choices` is a list of two or more choices. An exception is raised
        from this exception if a list of length one is given. The universe
        may impload if that happens.

    Arguments:
        key: The config key.
        value: The value given in the config.
        must: If the value must have been something set this to be that
            thing. Defaults to `None`. See `ConfigInvalid` for an example.
        choices: A list of two or more valid values for the config. If
            there are only two choices they will be listed as
            `'either A or B'`. If there are three or more choices they
            will be listed as a comma separated list with and oxford comma
            and an or for the last choice.
        quote: If `True` add double quotes to the choices. Defaults to
            `True`.
        config_desc: The description of the config if needed. Defaults to
            an empty string.

    Raises:
        ValueError: When the number of choices is invalid.
    """

    def __init__(self, key: str, value: Any, choices: list[Any],  # noqa: D107
                 quote: bool = True, config_desc: str = ''):
        if quote:
            choices = [_double_quote(c) for c in choices]
        if len(choices) == 2:
            must = f'be either {" or ".join(choices)}'
        elif len(choices) >= 3:
            must = f'be {", ".join(choices[:-1])}, or {choices[-1]}'
        else:
            raise ValueError('Invalid number of choices')
        super().__init__(key, value, must=must, config_desc=config_desc)


class ConfigInvalidPath(ConfigInvalid):
    """Invalid file system path configuation exception.

    Note:
        One or more of `bad_format`, `exist`, or `writable` must be `True`
        or an exception is raised from this exception . The universe may
        impload if that happens.

    Arguments:
        key: The config key.
        value: The value given in the config.
        exist: If `True` the path must exist. Defaults to `True`.
        writable: If `True` the path must be writable. Defaults to `False`.
        bad_format: If `True` the format of `value` is invalid. Defaults to
            `False`.
        is_type: If set the message will be phrased as needing to be the
            value of `is_type`. Defaults to an empty string.
        config_desc: The description of the config if needed. Defaults to
            an empty string.

    Raises:
        ValueError: When one or more of `bad_format`, `exist`, or `writable`
            must be True.
    """

    def __init__(self, key: str, value: str, exist: bool = True,  # noqa: D107
                 writable: bool = False, bad_format: bool = False,
                 is_type: str = '', config_desc: str = ''):
        if bad_format:
            super().__init__(key, value,
                             must='be a file system path',
                             config_desc=config_desc)
            return
        if writable and is_type:
            must = f'exist and be a {is_type} writable by CertDeploy'
        elif writable:
            must = 'exist and be writable by CertDeploy'
        elif exist and is_type:
            must = f'be a {is_type} that exists'
        elif exist:
            must = 'exist'
        else:
            raise ValueError('One or more of `bad_format`, `exist`, or '
                             '`writable` must be True.')
        super().__init__(key, value, must=must, config_desc=config_desc)
