
class CertDeployError(Exception):
    """CertDeploy specific error."""


class ConfigError(CertDeployError):
    """Configuration error"""


class ConfigErrorInvalid(ConfigError):

    def __init__(self, key, value, must_be=None):
        if must_be:
            super().__init__(f'Invalid value "{value}" for `{key}`. `{key}` '
                             f'must be {must_be}.')
        else:
            super().__init__(f'Invalid value "{value}" for `{key}`.')
