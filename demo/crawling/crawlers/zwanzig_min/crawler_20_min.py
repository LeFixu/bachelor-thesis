"""This module contains the crawler for the online news page 20min.ch"""

from ...utils.db_driver.source import Source
from .parsing import parse_article_or_news_ticker
from ...utils.web_scraping.web_scraping import (
    WebScraper,
    WebScraperConfiguration,
    ScraperDomainConfiguration,
)
from ...utils.web_scraping.run_configuration import RunConfiguration
from ...utils.file_location_helper import get_location_of_file


class Crawler20Min(WebScraper):
    """
    This DS implements functionality to crawl the webpage of 20min.ch
    and to orderly store the found data
    """

    def __init__(self, run_config: RunConfiguration):
        domain_config = ScraperDomainConfiguration(
            "https://www.20min.ch",
            get_location_of_file(__file__),
            Source.ZWANZIG_MIN,
            ["20min.ch/fr"],
        )

        config = WebScraperConfiguration(
            "20min.ch",
            domain_config,
            run_config,
            parse_article_or_news_ticker,
        )

        WebScraper.__init__(self, config)
