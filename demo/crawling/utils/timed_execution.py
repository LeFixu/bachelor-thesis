"""
This module stores the "execute_for_time function"
"""
from time import time, sleep
from typing import Callable, Awaitable, TypeVar
from asyncio import sleep as sleep_async
import logging as log


def execute_at_least_for_time(
    callable_: Callable[[], None], time_in_seconds: float
) -> None:
    """
    This function ensures, that the given callable takes at least time_in_seconds to exectue.
    The callable is executed immediately. If it finishes before the specified time,
    the thread is put to sleep for the rest of the time.
    """
    start_time = time()
    callable_()
    end_time = time()

    duration = end_time - start_time
    if duration > time_in_seconds:
        log.debug(
            "Period took longer (%fs) than configured periodicity (%fs).",
            duration,
            time_in_seconds,
        )
        return

    sleep_duration = time_in_seconds - duration
    log.debug(
        "Period took %fs. Sleeping for %fs to match configured periodicity of %fs.",
        duration,
        sleep_duration,
        time_in_seconds,
    )
    sleep(sleep_duration)


T = TypeVar("T")


async def execute_at_least_for_time_async(
    awaitable_: Awaitable[T], time_in_seconds: float
) -> T:
    """
    This function ensures, that the given callable takes at least time_in_seconds to exectue.
    The callable is executed immediately. If it finishes before the specified time,
    the thread is put to sleep for the rest of the time.
    """

    start_time = time()
    ret_val = await awaitable_
    end_time = time()

    duration = end_time - start_time
    if duration > time_in_seconds:
        log.debug(
            "Period took longer (%fs) than configured periodicity (%fs).",
            duration,
            time_in_seconds,
        )
        return ret_val

    sleep_duration = time_in_seconds - duration
    log.debug(
        "Period took %fs. Sleeping for %fs to match configured periodicity of %fs.",
        duration,
        sleep_duration,
        time_in_seconds,
    )
    await sleep_async(sleep_duration)
    return ret_val
