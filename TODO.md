
# Production

# Whenever
* Client connect retry: retry count, retry interval
* Per client fail_fast override
* parameterize ConfigError to make messages more uniform.
    ```
    def _must_be(types):
        if len(types) == 1:
            return f'must be a {_get_type_name(types[0])}'
        if len(types) == 2:
            return (f'must be a {_get_type_name(types[0])} or '
                    f'{_get_type_name(types[1])}')
        names = [_get_type_name(t) for t in types]
        return f'must be a {", ".join(names[:-1])} or {names[-1]}'

    ```
* Pre-commit:
    * bandit
    * python-safety-dependencies-check
    * dockerfilelint
