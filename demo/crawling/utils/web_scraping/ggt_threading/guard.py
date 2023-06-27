"""
This module contains the Guard thread, which can be used to monitor the state
of a list of GgtThreads
"""

from typing import Iterable, List
import logging as log
from ...timed_execution import execute_at_least_for_time
from .ggt_thread import GgtThread
from .status import Status


class Guard(GgtThread):
    """Thread guarding other threads"""

    _keep_running: bool
    _threads_to_watch: List[GgtThread]
    _patrol_frequency: float

    def __init__(
        self, threads_to_watch: Iterable[GgtThread], patrol_frequency: float = 2.0
    ):
        GgtThread.__init__(self, "guard")

        self._keep_running = True
        self._threads_to_watch = list(threads_to_watch)
        self._patrol_frequency = patrol_frequency

    def loop(self) -> None:
        while self._keep_running:
            execute_at_least_for_time(self._patrol, self._patrol_frequency)

    def _patrol(self) -> None:
        current_states = list(map(lambda thread: thread.status, self._threads_to_watch))
        thread_states_gt_running = [
            status.value > Status.RUNNING.value for status in current_states
        ]

        if not any(thread_states_gt_running):
            return

        if any(x == Status.CRASHED for x in current_states):
            log.error("At least one thread has crashed!")
            self._status = Status.CRASHED
            crashed_threads = list(
                filter(lambda tr: tr.status == Status.CRASHED, self._threads_to_watch)
            )
            for thread in crashed_threads:
                log.error("Thread '%s' is in status '%s'", thread.name, thread.status)
        else:
            log.info(
                "At least one observed thread has finished running.\
                Shutting down all other threads..."
            )
            self._status = Status.STOPPING

        self._stop_all()

    def _stop_all(self) -> None:

        for thread in self._threads_to_watch:
            thread.stop()

        log.info("Sent stop signals to all threads. Waiting for termination.")
        for thread in self._threads_to_watch:
            thread.join()

        log.info("All threads have shut down. Terminating guard.")
        self.stop()
