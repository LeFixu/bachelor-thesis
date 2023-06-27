"""This module contains the crawler for the online news page 20min.ch"""

from os import path, listdir, remove
from typing import List, Union, Callable
from asyncio import Queue
import logging as log
from .crawling.ggt_crawler import (
    Crawler,
    CrawlerConfiguration,
    TargetConfiguration,
    OutConfiguration,
    PolitenessConfiguration,
)
from .ggt_threading.status import Status
from .files_processor.files_processor import FilesProcessor, FilesProcessorConfig
from .ggt_threading.guard import Guard
from .ggt_threading.ggt_thread import GgtThread
from .ggt_threading.ggt_statistics import (
    CrawlerCompositeStatistics,
    Statistician,
    DroppedReason,
)
from .crawling.downloaded_site import DownloadedSite
from .run_configuration import RunConfiguration
from ..db_driver.db_driver import get_urls
from ..db_driver.article import Article
from ..db_driver.source import Source


class ScraperDomainConfiguration:
    """Encodes the domain crawler specific configuration"""

    seed_url: str
    working_dir: str
    source: Source
    blacklist: List[str]

    def __init__(
        self,
        seed_url: str,
        working_dir: str,
        source: Source,
        blacklist: List[str],
    ) -> None:
        self.seed_url = seed_url
        self.working_dir = working_dir
        self.source = source
        self.blacklist = blacklist


class WebScraperConfiguration:
    """Wraps all configuration needed by the abstract crawler wrapper"""

    name: str
    domain_configuration: ScraperDomainConfiguration
    run_configuration: RunConfiguration
    parser_function: Callable[[str, str], Union[Article, DroppedReason]]

    def __init__(
        self,
        name: str,
        domain_configuration: ScraperDomainConfiguration,
        run_configuration: RunConfiguration,
        parser_function: Callable[[str, str], Union[Article, DroppedReason]],
    ) -> None:
        self.name = name
        self.domain_configuration = domain_configuration
        self.run_configuration = run_configuration
        self.parser_function = parser_function


class WebScraper:
    """
    Abstract wrapper for platform specific crawlers
    """

    name: str
    _guard: GgtThread
    _child_threads: List[GgtThread]

    def __init__(self, config: WebScraperConfiguration) -> None:
        self.name = config.name
        downloads_folder = config.domain_configuration.working_dir + "/downloads"

        exchange_queue: Queue[DownloadedSite] = Queue()

        history_file = config.domain_configuration.working_dir + "/crawler_history.log"
        if path.exists(history_file):
            remove(history_file)  # Remove old log file

        log.debug("Getting known urls from db...")
        currently_known_urls = get_urls(config.domain_configuration.source)
        url_strs = list(map(lambda url: url["url"], currently_known_urls))
        log.info("Starting with %d known urls in db", len(url_strs))

        statistics = CrawlerCompositeStatistics()

        target_config = TargetConfiguration(
            config.domain_configuration.seed_url,
            config.domain_configuration.blacklist,
            url_strs,
            5,
        )

        out_config = OutConfiguration(
            downloads_folder, exchange_queue, statistics.crawler_statistics
        )

        politeness_config = PolitenessConfiguration(
            max_connections=config.run_configuration.max_concurrent_requests,
            min_time_per_request=config.run_configuration.min_time_per_request,
        )

        crawler_config = CrawlerConfiguration(
            target_config, politeness_config, out_config
        )
        processor_config = FilesProcessorConfig(
            exchange_queue, 5.0, config.parser_function
        )

        _clean_downloads_folder(crawler_config.out_configuration.downloads_folder)

        statistics = CrawlerCompositeStatistics()

        if path.exists(history_file):
            remove(history_file)  # Remove old log file

        statistician = Statistician(statistics, history_file, 5.0)
        crawler = Crawler(crawler_config)

        files_processor = FilesProcessor(
            processor_config,
            statistics.processor_statistics,
        )

        self._guard = Guard([crawler, files_processor, statistician])

        self._child_threads = [crawler, files_processor, self._guard, statistician]

    def get_status(self) -> Status:
        """Get the current status of the guard"""
        return self._guard.status

    def start(self) -> None:
        """Start the crawling process"""
        for thread in self._child_threads:
            thread.start()

    def stop(self) -> None:
        """Manually stop the crawling process"""
        for thread in self._child_threads:
            thread.stop()

        log.debug("Joining child treads...")
        for thread in self._child_threads:
            thread.join()
        log.debug("Finished joining child threads")


def _clean_downloads_folder(path_to_folder: str) -> None:
    if not path.exists(path_to_folder):
        log.warning(
            "Can't clean folder '%s' because it does not exist!", path_to_folder
        )

    if not path.isdir(path_to_folder):
        log.critical("Path tho downloads folder '%s' is not a folder!", path_to_folder)
        raise ValueError(path_to_folder)

    files_in_dir = listdir(path_to_folder)
    html_files_in_dir = filter(
        lambda file_name: file_name.endswith(".html"), files_in_dir
    )

    cleaned_path_to_folder = path_to_folder
    if not cleaned_path_to_folder.endswith("/"):
        cleaned_path_to_folder += "/"

    for html_file in html_files_in_dir:
        remove(cleaned_path_to_folder + html_file)
