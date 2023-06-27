"""
This module contains the status enum, which is used in threads to indicate the status of the thread
"""

from enum import Enum


class Status(Enum):
    """Encode possible states of threads"""

    IDLE = 0
    RUNNING = 10
    STOPPING = 20
    CRASHED = 30
    FINISHED = 40
