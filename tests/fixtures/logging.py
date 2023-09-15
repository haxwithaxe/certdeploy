"""Logging and log message formatting utilities."""

import logging

from certdeploy import CERTDEPLOY_CLIENT_LOGGER_NAME, DEFAULT_LOG_FORMAT


def format_client_log_message(level: str, message: str) -> bytes:
    return (DEFAULT_LOG_FORMAT % dict(
        levelname=level,
        name=CERTDEPLOY_CLIENT_LOGGER_NAME,
        message=message
    )).encode()


def format_server_log_message(level: str, message: str) -> bytes:
    return (DEFAULT_LOG_FORMAT % dict(
        levelname=level,
        name=CERTDEPLOY_CLIENT_LOGGER_NAME,
        message=message
    )).encode()


# String from certdeploy.client.daemon.DeployServer.serve_forever
CLIENT_HAS_STARTED_MESSAGE: bytes = format_client_log_message(
    'INFO',
    'Listening for incoming connections at '
)
CLIENT_UPDATED_MESSAGE = format_client_log_message(
    'INFO',
    'Updated services'
)
SERVER_HAS_STARTED_MESSAGE: bytes = format_server_log_message(
    'DEBUG',
    'Server.serve_forever: one_shot='
)


def log_level_int(log_level: str) -> int:
    return getattr(logging, log_level)


def log_level_eq(log_level_1, log_level_2):
    return log_level_int(log_level_1) == log_level_int(log_level_2)


def log_level_gt(log_level_1, log_level_2):
    return log_level_int(log_level_1) > log_level_int(log_level_2)


def log_level_lt(log_level_1, log_level_2):
    return log_level_int(log_level_1) < log_level_int(log_level_2)
