"""This module contains the worker which crawls the web page in its own thread"""

from asyncio import Queue, sleep, run, gather
from typing import Iterable, MutableSet, List, Dict, Any, Optional
import logging as log
from uuid import uuid4 as uuid
from aiohttp import (
    ClientSession,
    ClientResponse,
    ServerDisconnectedError,
    ClientResponseError,
    ClientConnectorError,
    InvalidURL,
    ServerTimeoutError,
    ClientTimeout,
)
from .downloaded_site import DownloadedSite
from .url_extractor.url_extractor import get_all_urls_from_html
from ..ggt_threading.ggt_statistics import CrawlerStatistics
from ..ggt_threading.ggt_thread import GgtThread
from ..ggt_threading.status import Status
from ...timed_execution import execute_at_least_for_time_async


class PolitenessConfiguration:
    """Defines the load the crawler will put on the webpage"""

    max_connections: int
    min_time_per_request: float

    def __init__(
        self, max_connections: int = 1, min_time_per_request: float = 0
    ) -> None:
        self.max_connections = max_connections
        self.min_time_per_request = min_time_per_request


class OutConfiguration:
    """Defines the output of the crawler"""

    downloads_folder: str
    out_queue: Queue[DownloadedSite]
    statistics: CrawlerStatistics

    def __init__(
        self,
        downloads_folder: str,
        out_queue: Queue[DownloadedSite] = Queue(),
        statistics: CrawlerStatistics = CrawlerStatistics(),
    ) -> None:
        self.downloads_folder = downloads_folder
        self.out_queue = out_queue
        self.statistics = statistics


class TargetConfiguration:
    """Defines what the crawler should crawl and what not"""

    seed_url: str
    blacklist: List[str]
    known_urls: MutableSet[str]
    max_depth: int

    def __init__(
        self,
        seed_url: str,
        blacklist: Optional[List[str]],
        known_urls: Optional[List[str]],
        max_depth: int = -1,
    ) -> None:
        self.seed_url = seed_url
        self.blacklist = blacklist if blacklist is not None else []
        self.known_urls = set(known_urls) if known_urls is not None else set()
        self.max_depth = max_depth


class CrawlerConfiguration:
    """
    Wraps all separate configuration objects for the crawler
    """

    target_configuration: TargetConfiguration
    politeness_configuration: PolitenessConfiguration
    out_configuration: OutConfiguration

    def __init__(
        self,
        target_configuration: TargetConfiguration,
        politeness_configuration: PolitenessConfiguration,
        out_configuration: OutConfiguration,
    ) -> None:
        self.target_configuration = target_configuration
        self.politeness_configuration = politeness_configuration
        self.out_configuration = out_configuration


class Crawler(GgtThread):
    """Crawler to download complete site from _seed_url"""

    _politeness_config: PolitenessConfiguration
    _out_config: OutConfiguration
    _target_config: TargetConfiguration

    _client_args: Dict[str, Any]
    _urls: Queue[str]

    def __init__(self, crawler_config: CrawlerConfiguration) -> None:
        GgtThread.__init__(self, "crawler")

        self._urls = Queue[str]()
        self._status = Status.IDLE

        client_timeout = ClientTimeout(
            total=None,  # default value is 5 minutes, set to `None` for unlimited timeout
            sock_connect=10,  # How long to wait before an open socket allowed to connect
            sock_read=10,  # How long to wait with no data being read before timing out
        )

        self._client_args = dict(trust_env=True, timeout=client_timeout)

        self._target_config = crawler_config.target_configuration
        self._out_config = crawler_config.out_configuration
        self._politeness_config = crawler_config.politeness_configuration

    def loop(self) -> None:
        run(self._run_async())  # jump from sync to async

    async def _run_async(self) -> None:
        log.debug("Crawler thread is in async context now")
        async with ClientSession(**self._client_args) as session:
            await self._download_site_recursively(self._target_config.seed_url, session)

    def _get_urls_from_downloaded_site(
        self, downloaded_site: DownloadedSite
    ) -> list[str]:
        log.debug(downloaded_site)
        try:
            return get_all_urls_from_html(
                downloaded_site.path_to_file, downloaded_site.url, True
            )
        except Exception as exc:
            log.error(
                "Got excpetion while getting URLs from html file '%s'.",
                downloaded_site.path_to_file,
            )
            log.exception(exc)
            raise exc

    async def _task_based_worker(self, worker_id: int, session: ClientSession) -> None:
        log.info("Starting up worker task %d", worker_id)
        while self._keep_running:
            if self._urls.empty():
                break

            url = self._urls.get_nowait()
            await self._download_site_and_schedule_tasks_for_children(url, session)

            self._out_config.statistics.known_urls = len(self._target_config.known_urls)
            self._out_config.statistics.urls_in_queue = self._urls.qsize()

        log.info("Shutting down worker task %d", worker_id)

    async def _download_site_recursively(
        self, url: str, session: ClientSession
    ) -> None:
        # First, fill up task queue with initial request
        log.info("Getting page at seed url '%s' to populate url queue...", url)
        await self._download_site_and_schedule_tasks_for_children(url, session)
        log.info(
            "Successfully got page at seed url '%s' and populated url queue with %d urls",
            url,
            self._urls.qsize(),
        )

        # Then, schedule workers to continuously decrease queue
        try:
            log.info("Setting up workers...")
            workers = [
                self._task_based_worker(i, session)
                for i in range(self._politeness_config.max_connections)
            ]
            await gather(*workers, return_exceptions=False)
            log.info("All workers terminated")
        except Exception as exception:
            log.error("Unexpected exception while joining request queue! %s", exception)
            log.exception(exception)
            raise exception

    def _add_to_known_urls(self, links: Iterable[str]) -> None:
        for link in links:
            self._target_config.known_urls.add(link)
            self._out_config.statistics.known_urls_composition.add_occurence(link)

    def _get_new_wanted_urls(self, found_urls: Iterable[str]) -> list[str]:
        blacklist_filter = filter(
            lambda url: not self._is_in_blacklist(url), found_urls
        )
        if self._target_config.max_depth > -1:
            blacklist_filter = filter(
                lambda url: len(url.split("/")) <= self._target_config.max_depth,
                blacklist_filter,
            )

        return list(
            filter(
                lambda link: link not in self._target_config.known_urls,
                blacklist_filter,
            )
        )

    async def _download_site_and_schedule_tasks_for_children(
        self, url: str, session: ClientSession
    ) -> None:
        log.debug(
            "Starting '_download_site_and_schedule_tasks_for_children' for '%s'", url
        )
        awaitable_ = _safe_download_site(
            session, url, self._out_config.downloads_folder, self._out_config.statistics
        )

        if self._politeness_config.min_time_per_request > 0:
            downloaded_site = await execute_at_least_for_time_async(
                awaitable_, self._politeness_config.min_time_per_request
            )
        else:
            downloaded_site = await awaitable_

        if downloaded_site is None:
            return

        log.debug("Adding '%s' to out queue", downloaded_site)
        self._out_config.out_queue.put_nowait(downloaded_site)

        urls = self._get_urls_from_downloaded_site(downloaded_site)
        filtered_links = self._get_new_wanted_urls(urls)
        self._add_to_known_urls(filtered_links)

        await self._schedule_tasks(filtered_links)

    async def _schedule_tasks(self, urls: list[str]) -> None:
        for url in urls:
            self._urls.put_nowait(url)
            log.debug("Scheduled url to download '%s'", url)

    def _is_in_blacklist(self, url: str) -> bool:
        for blacklist_item in self._target_config.blacklist:
            if blacklist_item in url:
                return True

        return False


async def _save_to_file(downloads_folder: str, response: ClientResponse) -> str:
    html_content = await response.text("utf-8")
    file_name = uuid().hex + ".html"

    path_to_file = f"{downloads_folder}/{file_name}"

    log.debug("Attempt to save to file at '%s'", path_to_file)
    with open(path_to_file, mode="w", encoding="utf-8") as file_pointer:
        file_pointer.write(html_content)
    log.debug("Successfully wrote file to '%s'", path_to_file)
    return path_to_file


async def _download_site(
    session: ClientSession,
    url: str,
    downloads_folder: str,
    statistics: CrawlerStatistics,
) -> Optional[str]:
    if not url.startswith("https://"):
        url = f"https://{url}"

    async with session.get(url) as response:
        statistics.status_codes.add_occurence(response.status)

        if response.status == 429:
            log.critical("Got status 429: Too many requests!")
            raise LookupError("Blocked by server for spamming!")

        if response.status >= 400:
            log.warning("GET: %s ; Got status code: %d", url, response.status)
            return None
        try:
            return await _save_to_file(downloads_folder, response)
        except UnicodeDecodeError as exc:
            log.warning(
                "Error while decoding response from '%s' to utf-8: '%s'", url, exc
            )
            return None


async def _safe_download_site(
    session: ClientSession,
    url: str,
    downloads_folder: str,
    statistics: CrawlerStatistics,
) -> Optional[DownloadedSite]:
    while True:
        try:
            path_to_file = await _download_site(
                session, url, downloads_folder, statistics
            )

            if path_to_file is None:
                log.info("Unable to download '%s' and save to file!", url)
                return None

            log.debug(
                "Successfully downloaded '%s' and saved to '%s'", url, path_to_file
            )
            return DownloadedSite(url, path_to_file)
        except (
            ServerDisconnectedError,
            ClientResponseError,
            ClientConnectorError,
            InvalidURL,
            ServerTimeoutError,
        ) as err:
            wait_time = 2
            log.info(err)
            log.info("Connection lost on URL '%s' for reason '%s'", url, err)
            log.info("Waiting for %ds", wait_time)
            await sleep(wait_time)  # don't hammer the server
