"""Contains the parsing logic for 20min html files"""
# pylint: disable=duplicate-code

import logging as log
from functools import reduce
from re import findall
from datetime import datetime
from typing import Optional, Callable, Union
from time import mktime
from dateutil import parser
from bs4 import BeautifulSoup, ResultSet, PageElement
from ...utils.db_driver.article import Article, ArticleBuilder
from ...utils.db_driver.source import Source
from ...utils.web_scraping.ggt_threading.ggt_statistics import DroppedReason


def parse_article_or_news_ticker(
    path_to_file: str, url: str
) -> Union[Article, DroppedReason]:
    """
    Parse the 20min HTML file at the specified location as an article.
    Provide the url because it's needed to build the Article object
    and it's not encoded in the file.

    If the file could not be parsed as an Article object, a reason
    in form of a DroppedReason Enum is returned
    """
    article = _parse_article_file(path_to_file, url)
    if not isinstance(article, DroppedReason):
        return article

    news_ticker = _parse_news_ticker_file(path_to_file, url)
    if not isinstance(news_ticker, DroppedReason):
        return news_ticker

    return article


def _parse_news_ticker_file(
    article_path: str, url: str
) -> Union[Article, DroppedReason]:
    with open(article_path, encoding="utf-8") as file_pointer:
        soup = BeautifulSoup(file_pointer, "html.parser")

        if not _is_news_ticker(soup):
            return DroppedReason.NOT_AN_ARTICLE

        title = _get_news_ticker_title(soup)
        log.debug("News ticker title is '%s'", title)
        if title is None:
            return DroppedReason.NO_TITLE

        lead = _get_news_ticker_lead(soup)
        log.debug("News ticker lead is '%s'", lead)
        if lead is None:
            return DroppedReason.NO_LEAD

        published_str = _get_news_ticker_datetime(soup)
        if published_str is None:
            return DroppedReason.NO_PUBLISHED

        log.debug("News ticker published is '%s'", published_str)
        date_str = findall(r"(\d{1,2}\.\d{1,2}\.\d{4})", published_str)
        if len(date_str) < 1:
            return DroppedReason.NO_PUBLISHED

        published_datetime = datetime.strptime(date_str[0], "%d.%m.%Y")
        published_timestamp = int(mktime(published_datetime.timetuple()))

        author = _get_news_ticker_author(soup)
        if author is None:
            author = ""

        text = _get_news_ticker_text(soup)
        log.debug("News ticker text is '%s'", text)
        if text is None:
            return DroppedReason.NO_TEXT

        builder = ArticleBuilder()
        builder.with_title(title).with_lead(lead).with_url(url).with_published(
            published_timestamp
        ).with_author(author).with_text(text).with_source(Source.ZWANZIG_MIN.value)

        return builder.build()


def _parse_article_file(article_path: str, url: str) -> Union[Article, DroppedReason]:
    with open(article_path, encoding="utf-8") as file_pointer:
        soup = BeautifulSoup(file_pointer, "html.parser")

        if not _is_article(soup):
            return DroppedReason.NOT_AN_ARTICLE

        title = _get_article_title(soup)
        log.debug("Article title is '%s'", title)
        if title is None:
            return DroppedReason.NO_TITLE

        lead = _get_article_lead(soup)
        log.debug("Article lead is '%s'", lead)
        if lead is None:
            return DroppedReason.NO_LEAD

        published_str = _get_article_datetime(soup)
        log.debug("Article published is '%s'", published_str)
        if published_str is None:
            return DroppedReason.NO_PUBLISHED

        published_datetime = parser.parse(published_str)
        published_timestamp = int(mktime(published_datetime.timetuple()))

        author = _get_article_author(soup)
        if author is None:
            author = ""

        text = _get_article_text(soup)
        log.debug("Article text is '%s'", text)
        if text is None:
            return DroppedReason.NO_TEXT

        builder = ArticleBuilder()
        builder.with_title(title).with_lead(lead).with_url(url).with_published(
            published_timestamp
        ).with_author(author).with_text(text).with_source(Source.ZWANZIG_MIN.value)

        return builder.build()


# pylint: disable=unnecessary-lambda-assignment


def _get_article_title(soup: BeautifulSoup) -> Optional[str]:
    extractor = lambda element: element.h2.text
    return _get_text_from_element(soup, "Article_elementTitle__INyMX", extractor)


def _get_news_ticker_title(soup: BeautifulSoup) -> Optional[str]:
    extractor = lambda element: element.text
    return _get_text_from_element(soup, "TickerContent_tickerTitle__hET1s", extractor)


def _get_article_datetime(soup: BeautifulSoup) -> Optional[str]:
    extractor = lambda element: element.attrs["datetime"]
    return _get_text_from_element(soup, "sc-xrami0-1", extractor)


def _get_news_ticker_datetime(soup: BeautifulSoup) -> Optional[str]:
    extractor = lambda element: element.text
    return _get_text_from_element(soup, "TickerDate_dateString__fk1Wg", extractor)


def _get_article_lead(soup: BeautifulSoup) -> Optional[str]:
    extractor = lambda element: element.p.text
    return _get_text_from_element(soup, "Article_elementLead__mvvHR", extractor)


def _get_news_ticker_lead(soup: BeautifulSoup) -> Optional[str]:
    extractor = lambda element: element.p.text
    return _get_text_from_element(soup, "TickerContent_tickerLead__kg__F", extractor)


def _get_article_author(soup: BeautifulSoup) -> Optional[str]:
    extractor = lambda element: element.text
    return _get_text_from_element(soup, "sc-1bbik4d-5", extractor)


def _get_news_ticker_author(soup: BeautifulSoup) -> Optional[str]:
    return _get_article_author(soup)


def _get_article_text(soup: BeautifulSoup) -> Optional[str]:
    extractor = lambda element: element.p.text
    return _get_text_from_elements(
        soup, "Article_elementTextblockarray__PafgJ", extractor
    )


def _get_news_ticker_text(soup: BeautifulSoup) -> Optional[str]:
    extractor = lambda element: element.p.text if element.p is not None else ""
    return _get_text_from_elements(soup, "tickerEvent_element__y2lg3", extractor)


# pylint: enable=unnecessary-lambda-assignment


def _get_text_from_element(
    soup: BeautifulSoup,
    class_name: str,
    extractor: Callable[[ResultSet[PageElement]], str],
) -> Optional[str]:
    elements = soup.find_all(class_=class_name)

    if len(elements) < 1:
        return None

    element = elements[0]
    return extractor(element)


def _get_text_from_elements(
    soup: BeautifulSoup,
    class_name: str,
    extractor: Callable[[ResultSet[PageElement]], str],
) -> Optional[str]:
    elements = soup.find_all(class_=class_name)

    if len(elements) < 1:
        return None

    texts = map(extractor, elements)
    concat_text = reduce(lambda a, b: a + " " + b, texts)
    return concat_text


def _is_article(soup: BeautifulSoup) -> bool:
    return _class_exists(soup, "Article_article__1qXvm")


def _is_news_ticker(soup: BeautifulSoup) -> bool:
    return _class_exists(soup, "TickerContent_ticker__M6alJ")


def _class_exists(soup: BeautifulSoup, html_class: str) -> bool:
    elements = soup.find_all(class_=html_class)
    return len(elements) > 0


# pylint: enable=duplicate-code
