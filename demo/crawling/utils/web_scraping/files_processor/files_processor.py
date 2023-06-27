"""
Module containing the FilesProcessor class
"""
from asyncio import Queue, QueueEmpty
from os import path, remove
import logging as log
from typing import List, Callable, Union
from ...db_driver.article import Article
from ...db_driver.db_driver import insert_articles
from ...timed_execution import execute_at_least_for_time
from ..ggt_threading.ggt_thread import GgtThread
from ..ggt_threading.status import Status
from ..crawling.downloaded_site import DownloadedSite
from ..ggt_threading.ggt_statistics import DroppedReason, ProcessorStatistics


class FilesProcessorConfig:
    """
    Encodes the configuration for the files processor
    """

    downloaded_files: Queue[DownloadedSite]
    upload_periodicity: float
    parser_function: Callable[[str, str], Union[Article, DroppedReason]]

    def __init__(
        self,
        downloaded_files: Queue[DownloadedSite],
        upload_periodicity: float,
        parser_function: Callable[[str, str], Union[Article, DroppedReason]],
    ) -> None:
        self.downloaded_files = downloaded_files
        self.upload_periodicity = upload_periodicity
        self.parser_function = parser_function


class FilesProcessor(GgtThread):
    """Thread parsing and saving articles to db"""

    _config: FilesProcessorConfig
    _statistics: ProcessorStatistics

    @property
    def statistics(self) -> ProcessorStatistics:
        """Get the ProcessorStatistics object"""
        return self._statistics

    def __init__(
        self,
        processor_config: FilesProcessorConfig,
        statistics: ProcessorStatistics,
    ) -> None:
        GgtThread.__init__(self, "files processor")

        self._status = Status.IDLE
        self._keep_running = True
        self._config = processor_config
        self._statistics = statistics

    def loop(self) -> None:
        while self._keep_running:
            execute_at_least_for_time(
                self._execute_once, self._config.upload_periodicity
            )

    def _execute_once(self) -> None:
        downloads = self._get_downloaded_sites_from_queue()
        articles: List[Article] = []
        paths_to_html_files = []
        for downloaded in downloads:
            log.debug("Processing '%s'", downloaded.url)
            if not path.exists(downloaded.path_to_file):
                log.error(
                    "Cannot parse file '%s' (%s) because it doesn't exist.",
                    downloaded.path_to_file,
                    downloaded.url,
                )
                continue
            paths_to_html_files.append(downloaded.path_to_file)
            article_or_reason = self._config.parser_function(
                downloaded.path_to_file, downloaded.url
            )
            if isinstance(article_or_reason, DroppedReason):
                log.debug(
                    "File at '%s' (%s) does not represent an article.",
                    downloaded.path_to_file,
                    downloaded.url,
                )
                self._statistics.dropped_statistics.increment_based_on(
                    article_or_reason
                )
                self._statistics.dropped_statistics.add_dropped_url(
                    downloaded.url, article_or_reason
                )
                continue

            log.debug("Saving article from '%s' into DB...", downloaded.url)
            articles.append(article_or_reason)

        log.debug("Trying to insert %d articles and urls...", len(articles))
        if len(articles) > 0:
            insert_articles(articles)
            self._statistics.files_uploaded += len(articles)
        log.info("Successfully inserted %d articles and urls", len(articles))

        log.debug("Trying to remove %d html files...", len(paths_to_html_files))
        _remove_files(paths_to_html_files)
        log.info("Successfully removed %d html files", len(paths_to_html_files))

        self._statistics.files_parsed += len(paths_to_html_files)

    def _get_downloaded_sites_from_queue(self) -> List[DownloadedSite]:
        result = []
        try:
            while True:
                result.append(self._config.downloaded_files.get_nowait())
        except QueueEmpty:
            return result


def _remove_files(paths_to_file: List[str]) -> None:
    for path_to_file in paths_to_file:
        if not path.exists(path_to_file):
            log.warning("Couldn't remove file '%s' because it doesn't exist!")
            return

        remove(path_to_file)
        log.debug("Successfully removed '%s'", path_to_file)
