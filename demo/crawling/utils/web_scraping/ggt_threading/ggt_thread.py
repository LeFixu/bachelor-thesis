"""This module provides the GgtThread abstract base class"""

from threading import Thread
import logging as log
from .status import Status


class GgtThread(Thread):
    """
    Abstract base class for threads used in crawling in this gender gap tracker
    """

    _name: str
    _status: Status
    _keep_running: bool

    def __init__(self, name: str) -> None:
        Thread.__init__(self)

        self._name = name
        self._status = Status.IDLE
        self._keep_running = True

    @property
    def status(self) -> Status:
        """Get the status of the thread"""
        return self._status

    def run(self) -> None:
        """Start the thread"""
        log.debug("Thread '%s' starts running...", self._name)
        try:
            self._status = Status.RUNNING
            self._keep_running = True

            self.loop()

            self._status = Status.FINISHED
        except Exception as err:
            self._status = Status.CRASHED
            log.critical(
                "Unexpected exception while running thread '%s': %s", self._name, err
            )
            log.exception(err)

        self._keep_running = False
        log.info("Finished running thread '%s'.", self._name)

    def stop(self) -> None:
        """Stop the thread gracefully"""
        log.info("Shutting thread '%s' down gracefully...", self._name)
        self._status = Status.STOPPING
        self._keep_running = False

    def loop(self) -> None:
        """Execution loop of the thread"""
        raise NotImplementedError("Call to abstract member!")
