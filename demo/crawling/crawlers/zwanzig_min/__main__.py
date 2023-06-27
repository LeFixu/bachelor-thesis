"""This main class serves to test the 20min crawler"""

from .crawler_20_min import Crawler20Min
from ...utils.web_scraping.news_portal_scraping import scrape_news_portal
from ...utils.web_scraping.run_configuration import DEFAULT_RUN_CONFIGURATION


if __name__ == "__main__":
    scraper_generator = lambda: Crawler20Min(DEFAULT_RUN_CONFIGURATION)
    scrape_news_portal(scraper_generator)
