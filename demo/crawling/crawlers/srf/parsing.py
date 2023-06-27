"""Contains the parsing logic for srf html files"""
# pylint: disable=duplicate-code
import logging as log
from functools import reduce
from typing import Optional, Callable, Union
from dateutil.parser import parse
from bs4 import BeautifulSoup, ResultSet, PageElement, Tag
from ...utils.db_driver.article import Article, ArticleBuilder
from ...utils.db_driver.source import Source
from ...utils.web_scraping.ggt_threading.ggt_statistics import DroppedReason


def parse_article_or_news_ticker(
    path_to_file: str, url: str
) -> Union[Article, DroppedReason]:
    """
    Parse the SRF HTML file at the specified location as an article.
    Provide the url because it's needed to build the Article object
    and it's not encoded in the file.

    If the file could not be parsed as an Article object, a reason
    in form of a DroppedReason Enum is returned
    """
    article = _parse_article_file(path_to_file, url)
    if not isinstance(article, DroppedReason):
        return article

    news_ticker = _parse_news_ticker_file(path_to_file)
    if not isinstance(news_ticker, DroppedReason):
        return news_ticker

    return article


def _parse_news_ticker_file(article_path: str) -> Union[Article, DroppedReason]:
    with open(article_path, encoding="utf-8") as file_pointer:
        soup = BeautifulSoup(file_pointer, "html.parser")

        if not _is_news_ticker(soup):
            return DroppedReason.NOT_AN_ARTICLE

        log.info("Skipping newsticker :(...")
        return DroppedReason.NO_TEXT


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
            lead = ""

        # somehow there are many leading and trailing whitespace characters involved in the lead...
        lead = lead.strip()

        published_timestamp = _get_article_published_datetime(soup)
        log.debug("Article published is '%s'", published_timestamp)
        if published_timestamp is None:
            return DroppedReason.NO_PUBLISHED

        modified_timestamp = _get_article_modified_datetime(soup)
        log.debug("Article published is '%s'", published_timestamp)

        text = _get_article_text(soup)
        log.debug("Article text is '%s'", text)
        if text is None:
            return DroppedReason.NO_TEXT

        author = _get_article_author(soup)
        if author is None:
            author = ""

        builder = ArticleBuilder()
        builder.with_title(title).with_lead(lead).with_url(url).with_published(
            published_timestamp
        ).with_author(author).with_text(text).with_source(Source.SRF.value)

        if modified_timestamp is not None:
            builder.with_updated(modified_timestamp)

        return builder.build()


# pylint: disable=unnecessary-lambda-assignment


def _get_article_title(soup: BeautifulSoup) -> Optional[str]:
    extractor = lambda element: element.text
    return _get_text_from_element(soup, "article-title__text", extractor)


# def _get_news_ticker_title(soup: BeautifulSoup) -> Optional[str]:
#     extractor = lambda element: element.text
#     return _get_text_from_element(soup, "TickerContent_tickerTitle__hET1s", extractor)


def _get_article_published_datetime(soup: BeautifulSoup) -> Optional[int]:
    try:
        published_str = soup.find_all("meta", {"property": "article:published_time"})[
            0
        ].attrs["content"]
        published = round(parse(published_str).timestamp())
        return published
    except Exception as err:
        log.warning("Couldn't parse published date because of error '%s'", err)
        return None


def _get_article_modified_datetime(soup: BeautifulSoup) -> Optional[int]:
    try:
        published_str = soup.find_all("meta", {"property": "article:modified_time"})[
            0
        ].attrs["content"]
        published = round(parse(published_str).timestamp())
        return published
    except Exception as err:
        log.info("Couldn't parse modified date because of error '%s'", err)
        return None


# def _get_news_ticker_datetime(soup: BeautifulSoup) -> Optional[str]:
#     extractor = lambda element: element.text
#     return _get_text_from_element(soup, "TickerDate_dateString__fk1Wg", extractor)


def _get_article_lead(soup: BeautifulSoup) -> Optional[str]:
    extractor = lambda element: element.text
    return _get_text_from_element(soup, "article-lead", extractor)


# def _get_news_ticker_lead(soup: BeautifulSoup) -> Optional[str]:
#     extractor = lambda element: element.p.text
#     return _get_text_from_element(soup, "TickerContent_tickerLead__kg__F", extractor)


def _get_article_author(soup: BeautifulSoup) -> Optional[str]:
    author_span = soup.find_all(attrs={"itemprop": "author"})
    if len(author_span) < 1:
        return None

    return str(author_span[0].text)


# def _get_news_ticker_author(soup: BeautifulSoup) -> Optional[str]:
#     return None


def _get_article_text(soup: BeautifulSoup) -> Optional[str]:
    article = soup.find(class_="article-content")
    if not isinstance(article, Tag):
        return None
    children = article.findChildren()

    paragraphs = []
    for child in children:
        if child.name == "p":
            paragraphs.append(child.text)
            continue

        ## Do not extract highlighted quotes, as they're already in the text
        # if child.name == "blockquote":
        #     quote_extractor = lambda blockquote: blockquote.text
        #     quote = _get_text_from_element(child, "blockquote__text", quote_extractor)

        #     text_extractor = lambda x: x.text
        #     quotee = _get_text_from_element(child, "blockquote__author", text_extractor)
        #     quotee_function = _get_text_from_element(
        #         child, "blockquote__function", text_extractor
        #     )

        #     text_to_append = (
        #         f'"{quote}"' + f", {quotee}"
        #         if quotee is not None
        #         else "" + f", {quotee_function}"
        #         if quotee_function is not None
        #         else ""
        #     )

        #     paragraphs.append(text_to_append)
        #     continue

        if child.name == "ul":
            list_elements = child.findChildren()
            texts = map(lambda list_element: str(list_element.text), list_elements)
            texts_stripped = map(lambda list_element: list_element.strip(), texts)
            texts_no_empty = filter(lambda text: len(text) > 0, texts_stripped)
            text_to_append = " ".join(texts_no_empty)
            paragraphs.append(text_to_append)
            continue

        continue

    return " ".join(paragraphs)


# def _get_news_ticker_text(soup: BeautifulSoup) -> Optional[str]:
#     extractor = lambda element: element.p.text if element.p is not None else ""
#     return _get_text_from_elements(soup, "tickerEvent_element__y2lg3", extractor)


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
    return _class_exists(soup, "article-content")


def _is_news_ticker(soup: BeautifulSoup) -> bool:
    return soup.find(id_="ticker") is not None


def _class_exists(soup: BeautifulSoup, html_class: str) -> bool:
    elements = soup.find_all(class_=html_class)
    return len(elements) > 0


# pylint: enable=duplicate-code
