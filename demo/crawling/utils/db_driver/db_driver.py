"""This module aims at providing an easy access to the mongoDB store used to save articles."""

import logging as log
from os import environ
from typing import Any, List, Optional, Callable, cast

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from .article import Article
from .url import Url, UrlBuilder
from .source import Source


def insert_article(article: Article) -> None:
    """Insert a single article"""
    log.debug("Inserting article '%s'...", article["title"])
    with _get_client() as client:
        articles_collection = _get_collection_articles(client)
        articles_collection.insert_one(article)
        log.info("Successfully inserted article '%s'!", article["title"])


def insert_articles(articles: List[Article]) -> None:
    """Insert a list of articles"""
    log.debug("Inserting '%d' articles...", len(articles))
    with _get_client() as client:
        articles_collection = _get_collection_articles(client)
        articles_collection.insert_many(articles)
        log.info("Successfully inserted '%d' articles!", len(articles))


def get_articles() -> List[Any]:
    """Get all articles"""
    log.debug("Getting all articles...")
    with _get_client() as client:
        collection = _get_collection_articles(client)
        result = list(collection.find())
        log.info("Successfully got '%d' articles!", len(result))
        return result


def print_top_n_articles(number: int) -> None:
    """Get top n articles"""
    log.debug("Getting top %d articles...", number)
    result_list = []
    with _get_client() as client:
        collection = _get_collection_articles(client)
        top_n = collection.find().limit(number)
        result_list = list(top_n)
        log.info("Successfully got top '%d' articles!", len(result_list))

    for result in result_list:
        print(result)


def _get_connection_string() -> str:
    log.debug("Getting connection string...")
    try:
        log.debug("Attempting to get full configuration from environment...")
        server = environ["GGT_MONGODB_SERVER"]
        port = environ["GGT_MONGODB_PORT"]
        database = environ["GGT_MONGODB_DATABASE"]
        username = environ["GGT_MONGODB_USER"]
        log.debug("Found all security-irrelevant properties in environment variables!")
    except KeyError:
        # fallback to default configuration for security-irrelevant properties
        log.debug("Security-irrelevant propertieys not found in environment variables!")
        server = "147.87.116.60"
        port = "27017"
        database = "articles"
        username = "paulus-the-workhorse"
        log.debug("Falling back to default configuration for server...")

    try:
        # attempt getting password
        log.debug("Attempting to get password from environment variables...")
        password = environ["GGT_MONGODB_PASSWORD"]
        log.debug("Successfully extracted mongoDB password from environment variables")
    except KeyError:
        # no password specified - return connection string to local db
        log.warning("Password not found in environment variables! Using local DB!")
        return "mongodb://localhost:27017/"

    log.debug("Return connection string to server")
    return f"mongodb://{username}:{password}@{server}:{port}/{database}"


def _get_client() -> MongoClient:

    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    connection_string = _get_connection_string()

    # Create a connection using MongoClient. You can import MongoClient or use
    # pymongo.MongoClient
    try:
        return MongoClient(connection_string)
    except ConnectionFailure as ex:
        log.exception(
            "Got 'ConnectionFailure' while trying to establish connection to mongo DB!"
        )
        log.info("Can't handle error in this context. Passing error on...")
        raise ex


def _get_database(client: MongoClient) -> Any:
    return client["articles"]


def _get_collection_articles(client: MongoClient) -> Any:
    database = _get_database(client)
    return database["articles"]


def get_urls(source: Optional[Source] = None) -> List[Url]:
    """Get all urls"""
    with _get_client() as client:
        collection = _get_collection_articles(client)

        aggregations = [
            {"$project": {"_id": "$_id", "source": "$source", "url": "$url"}}
        ]
        if source is not None:
            aggregations.insert(
                0,
                {
                    "$match": {
                        "source": source.value,
                    }
                },
            )
        result = collection.aggregate(aggregations)

        nullable_urls = map(_get_url_from_pymongo_result, result)
        non_null_urls = filter(lambda url: url is not None, nullable_urls)
        converter: Callable[[Optional[Url]], Url] = lambda nullable: cast(Url, nullable)
        urls = map(converter, non_null_urls)

        return list(urls)


def _get_url_from_pymongo_result(result: Any) -> Optional[Url]:
    builder = UrlBuilder()
    try:
        builder.with_id(result.get("_id")).with_source(result.get("source")).with_url(
            result.get("url")
        )

        return builder.build()
    except Exception as exception:
        log.warning("Cannot convert url result to Url object! Got : '%s'", exception)
        return None
