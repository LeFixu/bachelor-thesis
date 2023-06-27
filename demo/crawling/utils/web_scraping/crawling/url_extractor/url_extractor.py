"""
This module provides functionality to extract urls from a html page
All you need is the function get_all_urls_from_html
"""
import logging as log
from enum import Enum
from re import findall
from typing import Iterator, TypeVar, Optional, List
from bs4 import BeautifulSoup

T = TypeVar("T")


def get_all_urls_from_html(
    path_to_html_file: str, page_url: str, standardize: bool = True
) -> list[str]:
    # pylint: disable=line-too-long
    """
    Returns all urls from html file. Urls can also be relative.

    >>> get_all_urls_from_html("test/20min.html", "https://www.20min.ch/story/ehrenmann-und-respekt-fifa-boss-erntet-auch-zuspruch-fuer-rede-289370673555")
    ['www.20min.ch/', 'www.20min.ch/ausland', 'www.20min.ch/basel', 'www.20min.ch/bern', 'www.20min.ch/bundesratswahlen', 'www.20min.ch/cockpit', 'www.20min.ch/community', 'www.20min.ch/coopzeitung-weekend', 'www.20min.ch/coronavirus', 'www.20min.ch/digital', 'www.20min.ch/e-sport', 'www.20min.ch/gesundheit', 'www.20min.ch/influencer-radar', 'www.20min.ch/instagram-slider', 'www.20min.ch/kinostreaming', 'www.20min.ch/kochen', 'www.20min.ch/lifestyle/front', 'www.20min.ch/onelove', 'www.20min.ch/ostschweiz', 'www.20min.ch/people', 'www.20min.ch/schweiz', 'www.20min.ch/sport', 'www.20min.ch/sport/fussball', 'www.20min.ch/sport/fussball/wm-2022', 'www.20min.ch/story/gianni-infantino-wird-kritisiert-721929960264', 'www.20min.ch/story/wie-fifa-praesident-infantino-die-ganz-grossen-der-weltpolitik-traf-400537310807', 'www.20min.ch/ukraine', 'www.20min.ch/video/aktuell', 'www.20min.ch/video/live-tv', 'www.20min.ch/wettbewerbe', 'www.20min.ch/wirsindzukunft', 'www.20min.ch/wirtschaft', 'www.20min.ch/wissen', 'www.20min.ch/zentralschweiz', 'www.20min.ch/zuerich']

    >>> get_all_urls_from_html("test/srf.html", "https://www.srf.ch/allgemeines/newsletter-uebersicht-das-bringen-euch-die-srf-newsletter/#traditionalRegistration")
    ['www.srf.ch/', 'www.srf.ch/allgemeines/newsletter-uebersicht-das-bringen-euch-die-srf-newsletter', 'www.srf.ch/audio', 'www.srf.ch/hilfe', 'www.srf.ch/hilfe/kontakt', 'www.srf.ch/hilfe/website-und-apps/srf-apps', 'www.srf.ch/impressum', 'www.srf.ch/kids', 'www.srf.ch/kultur', 'www.srf.ch/meteo', 'www.srf.ch/news', 'www.srf.ch/news/verkehrsinformationen', 'www.srf.ch/play', 'www.srf.ch/play/tv', 'www.srf.ch/play/tv/programm', 'www.srf.ch/programm/radio', 'www.srf.ch/radio-srf-1', 'www.srf.ch/radio-srf-2-kultur', 'www.srf.ch/radio-srf-3', 'www.srf.ch/radio-srf-4-news', 'www.srf.ch/radio-srf-musikwelle', 'www.srf.ch/radio-srf-virus', 'www.srf.ch/rechtliches', 'www.srf.ch/school', 'www.srf.ch/sendungen/archiv', 'www.srf.ch/sendungen/dok', 'www.srf.ch/sendungen/hallosrf', 'www.srf.ch/sport', 'www.srf.ch/tv/tv-korrekturen', 'www.srf.ch/unternehmen', 'www.srf.ch/wissen']
    """
    # pylint: enable=line-too-long

    log.debug(
        "Extracting URLs from '%s', content of '%s' with option standardize %s",
        path_to_html_file,
        page_url,
        standardize,
    )
    domain = get_domain_from_url(page_url)

    urls = []
    with open(path_to_html_file, encoding="utf-8") as file_pointer:
        soup = BeautifulSoup(file_pointer, "html.parser")
        urls = _get_all_urls_from_domain(soup, domain)

        if standardize:
            standardized_urls = _get_standardized_urls(urls, page_url)
            urls = _filter_for_non_none(standardized_urls)

    sorted_distinct = sorted(_distinct(urls))
    log.debug(
        "Extracted %d urls from file '%s'", len(sorted_distinct), path_to_html_file
    )
    return sorted_distinct


def get_domain_from_url(url: str) -> str:
    # pylint: disable=line-too-long
    """Get the domain part from the url

    >>> get_domain_from_url("https://www.20min.ch")
    'www.20min.ch'

    >>> get_domain_from_url("https://www.20min.ch/")
    'www.20min.ch'

    >>> get_domain_from_url("https://www.20min.ch/bern?lang=de")
    'www.20min.ch'

    >>> get_domain_from_url("https://20min.ch/bern?lang=de")
    '20min.ch'

    >>> get_domain_from_url("epaper.20minuten.ch/#editions/644/Region%20Z%C3%BCrich")
    'epaper.20minuten.ch'

    >>> get_domain_from_url("https://www.20min.ch/story/ehrenmann-und-respekt-fifa-boss-erntet-auch-zuspruch-fuer-rede-289370673555")
    'www.20min.ch'
    """
    # pylint: enable=line-too-long
    url_without_protocol = _get_url_without_protocol(url)
    domain = url_without_protocol.split("/")[0]

    return domain


def _filter_for_non_none(list_to_filter: Iterator[Optional[T]]) -> List[T]:
    return_val: List[T] = []
    for item in list_to_filter:
        if item is not None:
            return_val.append(item)

    return return_val


class _UrlType(Enum):
    ABSOLUTE_WITHOUT_PROTOCOL = "ABSOLUTE_WITHOUT_PROTOCOL"  # www.20min.ch or 20min.ch
    ABSOLTUE_WITH_PROTOCOL = "ABSOLTUE_WITH_PROTOCOL"  # https://20min.ch
    RELATIVE_FROM_ROOT = "RELATIVE_FROM_ROOT"  # /lifestyle/front
    RELATIVE_FROM_PATH = (
        "RELATIVE_FROM_PATH"  # lifestyle/front or ./lifestyle/front or ../ausland
    )
    NOT_HTTP = "NOT_HTTP"


_PROTOCOL_DOMAIN_SEPARATOR = "://"


def _distinct(elements: list[T]) -> list[T]:
    """Get a distinct version of the list (without duplicates)

    >>> _distinct([1, 2, 2, 3, 4, 5, 5])
    [1, 2, 3, 4, 5]"""
    return list(set(elements))


def _is_absolute_url(url: str) -> bool:
    """Checks if a given url is absolute

    >>> _is_absolute_url("https://www.20min.ch/bern")
    True

    >>> _is_absolute_url("http://www.20min.ch/bern")
    True

    >>> _is_absolute_url("https://www.20min.ch/bern?lang=de")
    True

    >>> _is_absolute_url("www.20min.ch/bern")
    True

    >>> _is_absolute_url("20min.ch")
    True

    >>> _is_absolute_url("/bern")
    False

    >>> _is_absolute_url("bern")
    False

    >>> _is_absolute_url("../bern")
    False

    >>> _is_absolute_url("nunzia.barral@20minutes.ch")
    False

    >>> _is_absolute_url("mailto:alpamare@alpamare.ch")
    False

    >>> _is_absolute_url("file:/C:/Users/aowd/Downloads/pp_sfv_wald_und_wild_2017_definitiv.pdf")
    False

    >>> _is_absolute_url("tel://0791234567")
    False
    """
    url_type = _get_url_type(url)

    return url_type in (
        _UrlType.ABSOLTUE_WITH_PROTOCOL,
        _UrlType.ABSOLUTE_WITHOUT_PROTOCOL,
    )


def _get_url_type(url: str) -> _UrlType:
    """Get the type of the given url

    >>> _get_url_type("http://20min.ch")
    <_UrlType.ABSOLTUE_WITH_PROTOCOL: 'ABSOLTUE_WITH_PROTOCOL'>

    >>> _get_url_type("https://20min.ch")
    <_UrlType.ABSOLTUE_WITH_PROTOCOL: 'ABSOLTUE_WITH_PROTOCOL'>

    >>> _get_url_type("20min.ch")
    <_UrlType.ABSOLUTE_WITHOUT_PROTOCOL: 'ABSOLUTE_WITHOUT_PROTOCOL'>

    >>> _get_url_type("/bern/koeniz")
    <_UrlType.RELATIVE_FROM_ROOT: 'RELATIVE_FROM_ROOT'>

    >>> _get_url_type("bern/koeniz")
    <_UrlType.RELATIVE_FROM_PATH: 'RELATIVE_FROM_PATH'>

    >>> _get_url_type("../bern/koeniz")
    <_UrlType.RELATIVE_FROM_PATH: 'RELATIVE_FROM_PATH'>

    >>> _get_url_type("nunzia.barral@20minutes.ch")
    <_UrlType.NOT_HTTP: 'NOT_HTTP'>

    >>> _get_url_type("mailto:alpamare@alpamare.ch")
    <_UrlType.NOT_HTTP: 'NOT_HTTP'>

    >>> _get_url_type("file:/C:/Users/aowd/Downloads/pp_sfv_wald_und_wild_2017_definitiv.pdf")
    <_UrlType.NOT_HTTP: 'NOT_HTTP'>

    >>> _get_url_type("tel://0791234567")
    <_UrlType.NOT_HTTP: 'NOT_HTTP'>

    >>> _get_url_type("../sudoku/schwer/")
    <_UrlType.RELATIVE_FROM_PATH: 'RELATIVE_FROM_PATH'>

    >>> _get_url_type("./sudoku/schwer/")
    <_UrlType.RELATIVE_FROM_PATH: 'RELATIVE_FROM_PATH'>
    """
    if url.startswith("http"):
        return _UrlType.ABSOLTUE_WITH_PROTOCOL

    if url.startswith("/"):
        return _UrlType.RELATIVE_FROM_ROOT

    if _PROTOCOL_DOMAIN_SEPARATOR in url:
        # Other protocols
        return _UrlType.NOT_HTTP

    if url.startswith("file:") or url.startswith("mailto:") or url.startswith("tel:"):
        return _UrlType.NOT_HTTP

    if "@" in url:
        return _UrlType.NOT_HTTP

    matches = findall(r"^[A-Za-z0-9\-_]+\.([A-Za-z0-9\-_]+\.?)+", url)
    if len(matches) > 0:
        return _UrlType.ABSOLUTE_WITHOUT_PROTOCOL

    return _UrlType.RELATIVE_FROM_PATH


def _get_url_without_protocol(url: str) -> str:
    """Get the url without the protocol (https://)

    >>> _get_url_without_protocol("https://20min.ch/bern")
    '20min.ch/bern'

    >>> _get_url_without_protocol("20min.ch/bern")
    '20min.ch/bern'

    >>> _get_url_without_protocol("https://www.20min.ch/bern?key1=value1&key2=value2")
    'www.20min.ch/bern?key1=value1&key2=value2'
    """
    split_url = url.split(_PROTOCOL_DOMAIN_SEPARATOR)
    if len(split_url) < 2:
        # The assumption is, that the url didn't contain a protocol part
        return url

    return split_url[1]


def _get_url_without_protocol_and_query(url: str) -> str:
    # pylint: disable=line-too-long
    """Get the url without the protocol (https://) and query parameter (?key1=value1&key2=value2)

    >>> _get_url_without_protocol_and_query("https://www.20min.ch/bern?key1=value1&key2=value2")
    'www.20min.ch/bern'

    >>> _get_url_without_protocol_and_query("../sudoku/schwer")
    '../sudoku/schwer'

    >>> _get_url_without_protocol_and_query("https://spiele.20min.ch/sudoku/")
    'spiele.20min.ch/sudoku'

    >>> _get_url_without_protocol_and_query("https://www.srf.ch/news/schweiz/debatte-um-co2-gesetz-treibhausgase-massnahmen-ja-aber-nicht-unbedingt-im-inland/#5608158-like")
    'www.srf.ch/news/schweiz/debatte-um-co2-gesetz-treibhausgase-massnahmen-ja-aber-nicht-unbedingt-im-inland'

    >>> _get_url_without_protocol_and_query("https://www.srf.ch/news/schweiz/debatte-um-co2-gesetz-treibhausgase-massnahmen-ja-aber-nicht-unbedingt-im-inland#5608158-like")
    'www.srf.ch/news/schweiz/debatte-um-co2-gesetz-treibhausgase-massnahmen-ja-aber-nicht-unbedingt-im-inland'

    >>> _get_url_without_protocol_and_query("https://www.srf.ch/news/international/arbeitsverbot-fuer-frauen-wie-reagiert-die-schweiz-auf-den-beschluss-der-taliban/#")
    'www.srf.ch/news/international/arbeitsverbot-fuer-frauen-wie-reagiert-die-schweiz-auf-den-beschluss-der-taliban'

    >>> _get_url_without_protocol_and_query("https://www.srf.ch/news/international/arbeitsverbot-fuer-frauen-wie-reagiert-die-schweiz-auf-den-beschluss-der-taliban/#signInTab")
    'www.srf.ch/news/international/arbeitsverbot-fuer-frauen-wie-reagiert-die-schweiz-auf-den-beschluss-der-taliban'
    """
    # pylint: enable=line-too-long
    url_without_protocol = _get_url_without_protocol(url)
    url_without_query = url_without_protocol.split("?")[0]
    url_without_hashtag = url_without_query.split("#")[0]

    if url_without_hashtag.endswith("/"):
        return url_without_hashtag[:-1]
    return url_without_hashtag


def _is_from_domain(url: str, domain: str, tree_depth: int = -1) -> bool:
    """Checks if the given url belongs to the given domain

    >>> _is_from_domain("https://www.20min.ch/bern", "20min.ch")
    True

    >>> _is_from_domain("https://20min.ch/bern", "20min.ch")
    True

    >>> _is_from_domain("https://api.20min.ch/login", "20min.ch")
    True

    >>> _is_from_domain("http://www.20min.ch/bern", "20min.ch")
    True

    >>> _is_from_domain("www.20min.ch/bern", "20min.ch")
    True

    >>> _is_from_domain("gutscheine.20min.ch", "www.20min.ch")
    False

    >>> _is_from_domain("https://www.20min.ch/bern", "www.20min.ch")
    True

    >>> _is_from_domain("gutscheine.20min.ch", "www.20min.ch", 2)
    True

    >>> _is_from_domain("https://20min.ch/bern", "www.20min.ch")
    False

    >>> _is_from_domain("https://api.20min.ch/login", "www.20min.ch")
    False

    >>> _is_from_domain("http://www.20min.ch/bern", "www.20min.ch")
    True

    >>> _is_from_domain("epaper.20minuten.ch/#editions/644/Region%20Z%C3%BCrich", "www.20min.ch", 2)
    False

    >>> _is_from_domain("epaper.20min.ch/#editions/644/Region%20Z%C3%BCrich", "www.20min.ch", 2)
    True

    >>> _is_from_domain("www.20min.ch/bern", "www.20min.ch")
    True

    >>> _is_from_domain("api.20min.ch/login", "www.20min.ch")
    False

    >>> _is_from_domain("gutscheine.20min.ch/", "www.20min.ch")
    False

    >>> _is_from_domain("https://www.watson.ch/bern", "20min.ch")
    False

    >>> _is_from_domain("https://watson.ch/bern", "20min.ch")
    False

    >>> _is_from_domain("https://api.watson.ch/login", "20min.ch")
    False

    >>> _is_from_domain("http://www.watson.ch/bern", "20min.ch")
    False

    >>> _is_from_domain("www.watson.ch/bern", "20min.ch")
    False
    """

    top_n_domains = _get_top_n_levels_of_domain(domain, tree_depth)

    domain_of_url = get_domain_from_url(url)
    return domain_of_url.endswith(top_n_domains)


def _get_top_n_levels_of_domain(domain: str, n_levels: int) -> str:
    """Get top n levels of domain (cut away subdomains below level n)

    >>> _get_top_n_levels_of_domain("www.20min.ch", -1)
    'www.20min.ch'

    >>> _get_top_n_levels_of_domain("www.20min.ch", 0)
    ''

    >>> _get_top_n_levels_of_domain("www.20min.ch", 1)
    'ch'

    >>> _get_top_n_levels_of_domain("www.20min.ch", 2)
    '20min.ch'

    >>> _get_top_n_levels_of_domain("www.20min.ch", 3)
    'www.20min.ch'

    >>> _get_top_n_levels_of_domain("www.20min.ch", 4)
    'www.20min.ch'

    >>> _get_top_n_levels_of_domain("www.20min.ch", 400)
    'www.20min.ch'
    """
    domain_without_top_level_point = ".".join(
        domain.split(".")
    )  # transforms www.20min.ch. to www.20min.ch

    if n_levels < 0:
        return domain

    if n_levels == 0:
        return ""

    if domain_without_top_level_point.count(".") < n_levels - 1:
        return domain_without_top_level_point

    return ".".join(domain_without_top_level_point.split(".")[-n_levels:])


def _get_relative_urls(urls: list[str]) -> Iterator[str]:
    """Filter out the absolute urls and get only the relative urls

    >>> list(_get_relative_urls(["http://20min.ch/bern", "20min.ch/basel", "/lifestyle", "bern"]))
    ['/lifestyle', 'bern']
    """
    return filter(lambda url: not _is_absolute_url(url), urls)


def _get_all_urls_from_domain(
    soup: BeautifulSoup, domain: str, inclue_relative_links: bool = True
) -> list[str]:
    def _get_absolute_urls_from_domain(urls: list[str], domain: str) -> Iterator[str]:
        return filter(lambda url: _is_from_domain(url, domain), urls)

    link_elements = soup.find_all("a", href=True)
    all_urls: list[str] = list(map(lambda l: l["href"], link_elements))  # type: ignore

    absolute_urls = list(_get_absolute_urls_from_domain(all_urls, domain))

    if inclue_relative_links:
        relative_urls = _get_relative_urls(all_urls)
        absolute_urls += relative_urls

    return absolute_urls


def _get_standardized_urls(
    urls: list[str], current_page_url: str
) -> Iterator[Optional[str]]:
    # pylint: disable=line-too-long
    """
    Make a list of urls absolute. Already absolute urls will be returned as is

        Parameters:
            urls (list[str]): The list of urls to make absolute
            current_page_url (str): The url of the current page. The relative urls will be made absolute according to this location

    >>> list(_get_standardized_urls(["https://20min.ch/bern", "http://www.20min.ch/basel", "/ukraine", "bern", "20min.ch", "https://api.20min.ch/login", "api.20min.ch/login"], "https://www.20min.ch/lifestyle/mode?lang=de&anotherKey=anotherValue"))
    ['20min.ch/bern', 'www.20min.ch/basel', 'www.20min.ch/ukraine', 'www.20min.ch/lifestyle/mode/bern', '20min.ch', 'api.20min.ch/login', 'api.20min.ch/login']
    """
    # pylint: enable=line-too-long

    return map(lambda url: _get_standardized_url(url, current_page_url), urls)


def _get_standardized_url(url: str, current_page_url: str) -> Optional[str]:
    # pylint: disable=line-too-long
    """/usr/share/code/resources/app/out/vs/code/electron-sandbox/workbench/workbench.html
    >>> _get_standardized_url("../sudoku/schwer/", "https://spiele.20min.ch/sudoku/")
    'spiele.20min.ch/sudoku/../sudoku/schwer'

    >>> _get_standardized_url("mailto:info@spiele.20min.ch", "https://spiele.20min.ch/sudoku/") is None
    True

    >>> _get_standardized_url("/onelove/3-mit-drama", "https://www.20min.ch/onelove")
    'www.20min.ch/onelove/3-mit-drama'
    """
    # pylint: enable=line-too-long
    url_type = _get_url_type(url)
    match url_type:
        case _UrlType.ABSOLUTE_WITHOUT_PROTOCOL:
            return _get_url_without_protocol_and_query(url)
        case _UrlType.ABSOLTUE_WITH_PROTOCOL:
            return _get_url_without_protocol_and_query(url)
        case _UrlType.RELATIVE_FROM_ROOT:
            domain = get_domain_from_url(current_page_url)
            if not url.startswith("/"):
                url = "/" + url
            return domain + url
        case _UrlType.RELATIVE_FROM_PATH:
            cur_location = _get_url_without_protocol_and_query(current_page_url)
            if not url.startswith("/"):
                url = "/" + url
            return _get_url_without_protocol_and_query(cur_location + url)
        case _UrlType.NOT_HTTP:
            return None

    raise NotImplementedError(f"URL type '{url_type}' not implemented!")
