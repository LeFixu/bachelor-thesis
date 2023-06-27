"""This module contains functionality to start web scrapers"""
from logging import basicConfig, getLogger, FileHandler, Formatter
from time import sleep
import sys
from typing import Callable
from .web_scraping import WebScraper
from .run_configuration import get_log_level, print_run_configuration, get_max_run_time
from .ggt_threading.status import Status


LOG_FORMAT = "%(asctime)s [%(levelname)s]: %(message)s in %(pathname)s:%(lineno)d"


def scrape_news_portal(scraper_generator: Callable[[], WebScraper]) -> None:
    """Start and monitor the given web scraper"""

    print_run_configuration()
    _configure_root_logger()

    print("Generating web scraper...")
    scraper = scraper_generator()

    print(f"Starting {scraper.name} crawler...")
    scraper.start()

    counter: int = 0
    end_after_s = get_max_run_time()

    while True:
        status = scraper.get_status()
        print(f"Status: {status}")

        if status == Status.CRASHED:
            print("Crawler crashed!")
            sys.exit(1)

        if status not in (Status.RUNNING, Status.IDLE):
            print("Finished!")
            break

        sleep(1)
        print()

        counter += 1
        if counter > end_after_s:
            print("Top out!")
            scraper.stop()


def _configure_root_logger() -> None:
    log_level = get_log_level()

    basicConfig()
    getLogger().setLevel(log_level)
    file_handler = FileHandler("run.log", mode="w", encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(Formatter(LOG_FORMAT))
    getLogger().addHandler(file_handler)
