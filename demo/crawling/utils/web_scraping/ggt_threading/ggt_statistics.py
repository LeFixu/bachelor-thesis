"""
This module contains datastructures used to track the state of
crawlers
"""

from enum import Enum
from typing import Dict, Any, List
from json import dumps
from time import time
from ...timed_execution import execute_at_least_for_time
from .ggt_thread import GgtThread


class _ConvertableToDict:
    """Abstract base class forcing subclasses to impement toDict function"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert the current object to a dict"""
        raise NotImplementedError("Call to abstract method!")


class DroppedReason(Enum):
    """
    Enum encoding the reason an article could not be parsed and consequently why it was dropped
    """

    NOT_AN_ARTICLE = "NOT_AN_ARTICLE"
    NO_TITLE = "NO_TITLE"
    NO_LEAD = "NO_LEAD"
    NO_PUBLISHED = "NO_PUBLISHED"
    NO_AUTHOR = "NO_AUTHOR"
    NO_TEXT = "NO_TEXT"


class DroppedFilesStatistics(_ConvertableToDict):
    """Class that can be used to keep track of why files were dropped"""

    not_an_article: int = 0
    no_title: int = 0
    no_lead: int = 0
    no_published: int = 0
    no_author: int = 0
    no_text: int = 0
    dropped_articles: List[str] = []

    def add_dropped_url(self, url: str, reason: DroppedReason) -> None:
        """Log that a url has been dropped for a specified reason"""
        if reason != DroppedReason.NOT_AN_ARTICLE:
            self.dropped_articles.append(url)

    def increment_based_on(self, reason: DroppedReason) -> None:
        """Increment a drop reason"""
        match reason:
            case DroppedReason.NOT_AN_ARTICLE:
                self.not_an_article += 1
                return
            case DroppedReason.NO_TITLE:
                self.no_title += 1
                return
            case DroppedReason.NO_LEAD:
                self.no_lead += 1
                return
            case DroppedReason.NO_PUBLISHED:
                self.no_published += 1
                return
            case DroppedReason.NO_AUTHOR:
                self.no_author += 1
                return
            case DroppedReason.NO_TEXT:
                self.no_text += 1
                return

        raise NotImplementedError(f"Reason '{reason}' not implemented!")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "not_an_article": self.not_an_article,
            "no_title": self.no_title,
            "no_lead": self.no_lead,
            "no_published": self.no_published,
            "no_author": self.no_author,
            "no_text": self.no_text,
            "dropped_articles": self.dropped_articles,
        }


class ProcessorStatistics(_ConvertableToDict):
    """Encodes the statistics of the files processor"""

    files_parsed: int = 0
    files_uploaded: int = 0
    dropped_statistics: DroppedFilesStatistics = DroppedFilesStatistics()

    def to_dict(self) -> dict[str, Any]:
        return {
            "files_parsed": self.files_parsed,
            "files_uploaded": self.files_uploaded,
            "dropped_statistics": self.dropped_statistics.to_dict(),
        }


class CrawlerStatusCodesStatistics(_ConvertableToDict):
    """Encodes the encountered HTTP status codes returned from the server"""

    status_codes_occurences: Dict[str, int] = {}

    def add_occurence(self, status_code: int) -> None:
        """Add an occurence of a HTTP status code"""
        status_code_str = str(status_code)
        if status_code_str not in self.status_codes_occurences:
            self.status_codes_occurences[status_code_str] = 0

        self.status_codes_occurences[status_code_str] += 1

    def to_dict(self) -> dict[str, Any]:
        return self.status_codes_occurences


def _ensure_trailing_slash(url: str) -> str:
    if len(url) < 1 or url[-1:] == "/":
        return url

    return f"{url}/"


class UrlStatistics(_ConvertableToDict):
    """
    Class encoding statistics regarding a certain url.
    Url can be simplified to aggregate occurences
    """

    subdomain_occurences: Dict[str, int] = {}
    _path_depth: int

    def __init__(self, folder_depth: int = 1):
        self._path_depth = folder_depth

    def add_occurence(self, url: str) -> None:
        """Add an occurence of an url"""
        url_to_log = self._get_url_to_log(url)
        if url_to_log not in self.subdomain_occurences:
            self.subdomain_occurences[url_to_log] = 0

        self.subdomain_occurences[url_to_log] += 1

    def _get_url_to_log(self, url: str) -> str:
        """Transform url according to folder_depth"""
        url_parts = url.split("/")

        if self._path_depth < 1:
            return _ensure_trailing_slash(url_parts[0])

        if len(url_parts) < self._path_depth + 1:
            return _ensure_trailing_slash(url)

        ret_val = ""
        for i in range(self._path_depth + 1):
            if url_parts[i] == "":
                continue
            ret_val += f"{url_parts[i]}/"

        return _ensure_trailing_slash(ret_val)

    def to_dict(self) -> dict[str, Any]:
        return self.subdomain_occurences


class CrawlerStatistics(_ConvertableToDict):
    """Class encoding the crawler statistics"""

    urls_in_queue: int = 0
    known_urls: int = 0
    known_urls_composition: UrlStatistics = UrlStatistics()
    status_codes: CrawlerStatusCodesStatistics = CrawlerStatusCodesStatistics()

    def to_dict(self) -> dict[str, Any]:
        return {
            "urls_in_queue": self.urls_in_queue,
            "known_urls": self.known_urls,
            "known_urls_composition": self.known_urls_composition.to_dict(),
            "status_codes": self.status_codes.to_dict(),
        }


class CrawlerCompositeStatistics(_ConvertableToDict):
    """Class encoding crawler and processor_statistics"""

    crawler_statistics: CrawlerStatistics = CrawlerStatistics()
    processor_statistics: ProcessorStatistics = ProcessorStatistics()

    def to_dict(self) -> dict[str, Any]:
        return {
            "crawler_statistics": self.crawler_statistics.to_dict(),
            "processor_statistics": self.processor_statistics.to_dict(),
        }


class Statistician(GgtThread):
    """Thread writing statistics"""

    _statistics: CrawlerCompositeStatistics
    _path_to_history_file: str
    _reporting_frequency: float

    def __init__(
        self,
        statistics: CrawlerCompositeStatistics,
        path_to_log_file: str,
        reporting_frequency: float,
    ) -> None:
        GgtThread.__init__(self, "statistician")

        self._statistics = statistics
        self._reporting_frequency = reporting_frequency
        self._path_to_history_file = path_to_log_file

    def loop(self) -> None:
        while self._keep_running:
            execute_at_least_for_time(self._write_statistics, self._reporting_frequency)

    def _write_statistics(self) -> None:
        with open(self._path_to_history_file, "a", encoding="utf-8") as file_pointer:

            timed_statistics = {
                "date_time": round(time()),
                "statistics": self._statistics.to_dict(),
            }

            file_pointer.write(dumps(timed_statistics) + "\n")
