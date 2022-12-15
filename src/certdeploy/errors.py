
def _double_quote(value):
    return f'"{value}"'


class CertDeployError(Exception):
    """CertDeploy specific error."""


class ConfigError(CertDeployError):
    """Configuration error"""


class ConfigInvalid(ConfigError):

    def __init__(self, key, value, must=None, config_desc=''):
        if config_desc:
            config_desc = f'{config_desc} '
        if must:
            super().__init__(f'Invalid value "{value}" for {config_desc}'
                             f'`{key}`. `{key}` must {must}.')
        else:
            super().__init__(f'Invalid value "{value}" for {config_desc}'
                             f'`{key}`.')


class ConfigInvalidNumber(ConfigInvalid):

    def __init__(self, key, value, is_type='number', optional=False, gt=None,
                 lt=None, ge=None, le=None, config_desc=''):
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

    def __init__(self, key, value, choices, quote=True, config_desc=''):
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

    def __init__(self, key, value, exist=True, writable=False,
                 bad_format=False, is_type='', config_desc=''):
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
