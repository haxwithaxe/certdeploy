
import time

import schedule

from ..errors import ConfigError
from . import log
from .config import ServerConfig
from .renew import renew_certs

_UNITS = ('minute', 'hour', 'day', 'week')
_WEEKDAYS = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday',
             'sunday')


def _normalize_unit(unit: str, interval: int):
    """Convert `unit` to a plural if interval is not 1."""
    # `schedule` uses plurals for `minute`, `hour`, `day`, and `week` units but
    #   only when the interval is not 1, which is overly complicated. So the
    #   conversion is being done here to keep the docs and config simpler.
    norm_unit = unit.lower().strip()
    if norm_unit not in _WEEKDAYS + _UNITS:
        raise ConfigError('`renew_unit` needs to be a day of the week '
                          'or an interval unit (minute, hour, day, week) not: '
                          f'{unit}')
    if interval != 1:
        return f'{norm_unit}s'
    return norm_unit


def _validate_config(unit: str, interval: int):
    # Do some quick validation and throw helpful errors instead of random
    #   errors from `schedule`
    if unit in _WEEKDAYS and interval != 1:
        raise ConfigError('`renew_unit` cannot be a weekday if `renew_every` is'
                          ' set and not 1.')
    if not isinstance(interval, int) or interval < 1:
        raise ConfigError('`renew_every` must be an integer greater than 0 if'
                          f' it is set, not: {interval}')


def _schedule(interval: int, unit: str, at: str, action: callable,
              **action_kwargs):
    # Attempt to configure a scheduled job
    # Catch config related errors and add some context before reraising
    try:
        every = schedule.every(interval)
    except schedule.ScheduleValueError as err:
        raise ConfigError(f'Invalid `renew_every` value: {err}') from err
    try:
        when = getattr(every, unit)
    except schedule.ScheduleValueError as err:
        raise ConfigError(f'Invalid `renew_unit` value: {err}') from err
    if at:
        try:
            when = when.at(at)
        except schedule.ScheduleValueError as err:
            raise ConfigError(f'Invalid `renew_at` value: {err}') from err
    when.do(action, **action_kwargs)


def serve_forever(config: ServerConfig):
    """Trying to renew and deploy certs periodically.

    Arguments:
        config (ServerConfig): `ServerConfig`

    """
    log.info('Starting daemon.')
    unit = _normalize_unit(config.renew_unit, config.renew_every)
    _validate_config(unit, config.renew_every)
    log.info('Attempting to renew certs every %s %s at %s', config.renew_every,
             unit, config.renew_at)
    _schedule(config.renew_every, unit, config.renew_at, renew_certs,
              config=config)
    while True:
        schedule.run_pending()
        log.debug('schedule.idle_seconds() is %s', schedule.idle_seconds())
        time.sleep(schedule.idle_seconds() or 30)
