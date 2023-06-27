"""This module contains functions to get the run configuration of cralers"""

from os import environ
from logging import getLevelName, WARNING

DEFAULT_LOG_LEVEL = WARNING
DEFAULT_MAX_CONCURRENT_REQUESTS = 3
DEFAULT_MIN_TIME_PER_REQUEST = 0.5
DEFAULT_MAX_RUN_TIME = 14400  # 4h in seconds


def get_log_level() -> int:
    """
    Gets the log level from the defined environment variable
    GGT_LOG_LEVEL or the default value if not found
    """
    try:
        env_var = environ["GGT_LOG_LEVEL"]
        return int(getLevelName(env_var))
    except KeyError:
        return DEFAULT_LOG_LEVEL


def get_max_concurrent_requests() -> int:
    """
    Gets the max concurrent requests setting from the defined environment variable
    GGT_MAX_CONCURRENT_REQUESTS or the default value if not found
    """
    try:
        return int(environ["GGT_MAX_CONCURRENT_REQUESTS"])
    except KeyError:
        return DEFAULT_MAX_CONCURRENT_REQUESTS


def get_max_run_time() -> int:
    """
    Gets the max run time setting from the defined environment variable
    GGT_MAX_RUN_TIME or the default value if not found
    """
    try:
        return int(environ["GGT_MAX_RUN_TIME"])
    except KeyError:
        return DEFAULT_MAX_RUN_TIME


def get_min_time_per_request() -> float:
    """
    Gets the min time per request setting from the defined environment variable
    GGT_MIN_TIME_PER_REQUEST or the default value if not found
    """
    try:
        return float(environ["GGT_MIN_TIME_PER_REQUEST"])
    except KeyError:
        return DEFAULT_MIN_TIME_PER_REQUEST


def print_run_configuration() -> None:
    """Prints the currently set run configuration to stdout"""

    print(f"Max concurrent requests: {get_max_concurrent_requests()}")
    print(f"Min time per request: {get_min_time_per_request()}")
    print(f"Log level: {getLevelName(get_log_level())}")
    print(f"Max run time: {get_max_run_time()}")


class RunConfiguration:
    """Encodes the run configuration used to steer a crawler"""

    max_concurrent_requests: int
    min_time_per_request: float

    def __init__(
        self, max_concurrent_requests: int, min_time_per_request: float
    ) -> None:
        self.max_concurrent_requests = max_concurrent_requests
        self.min_time_per_request = min_time_per_request


DEFAULT_RUN_CONFIGURATION = RunConfiguration(
    get_max_concurrent_requests(), get_min_time_per_request()
)
