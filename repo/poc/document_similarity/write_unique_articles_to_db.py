"""This module aims at inserting unique articles from a json file to the DB"""

from os import PathLike, listdir, environ
from pathlib import Path
from typing import Iterable, Dict, Any, List
from re import search
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import logging as log
import ijson
from sys import argv



def __get_connection_string() -> str:
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


def __get_client() -> MongoClient:

    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    connection_string = __get_connection_string()

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

def __get_database(client: MongoClient) -> Any:
    return client["articles"]

def __is_clean_data_file(filename: str) -> bool:
    """
    >>> __is_clean_data_file('clean-data_20min_cosine.json')
    True
    >>> __is_clean_data_file('clean-data_Watson_cosine.json')
    True
    >>> __is_clean_data_file('clean-data_blick_cosine.json')
    True
    >>> __is_clean_data_file('clean-data_srf_cosine.json')
    True
    >>> __is_clean_data_file('some-random.json')
    False
    >>> __is_clean_data_file('some-file.py')
    False
    """
    return search("clean-data_\w+_cosine\.json", filename) is not None

def __get_unique_article_files(path: PathLike=".") -> Iterable[PathLike]:
    return filter(__is_clean_data_file, listdir(path))

def __get_collection(collection_name: str = "unique_articles") -> Any:
    client = __get_client()
    database = __get_database(client)
    return database[collection_name]

def __read_large_json_file(path: PathLike) -> List[Dict]:
    # load Data from JSON
    with open(path, 'rb') as file:
        return list(ijson.items(file, 'item'))

def insert_into_db(path: PathLike) -> None:
    """Insert data from a file into the db"""
    articles = __read_large_json_file(path)
    __get_collection().insert_many(articles)

if __name__ == "__main__" and len(argv) > 1:
    log.basicConfig(level=log.INFO)
    files = __get_unique_article_files(Path(argv[1]))
    for file in files:
        log.info("Writing data from '%s' into DB...", file)
        insert_into_db(file)
        log.info("Successfully worte data from '%s' into DB!", file)

if __name__ == "__main__" and len(argv) < 2:
    import doctest
    doctest.testmod()