"""Execute citation extraction"""
from os import environ
import sys
from logging import (
    getLevelName,
    WARNING,
    basicConfig,
    getLogger,
    FileHandler,
    Formatter,
)
import logging as log
from typing import Dict, Iterable, Any
from datetime import datetime
from multiprocessing import Pool as get_pool
from multiprocessing import cpu_count, Queue, Process
import signal
from queue import Empty
from .utils.db_driver.db_driver import (
    get_articles,
    insert_analyzed_article,
    get_analyzed_article_ids,
)
from .utils.db_driver.article import ArticleBuilder
from .functions.get_people_from_string import (
    get_people_from_string,
    get_person_from_string,
)
from .functions.get_genderized_person import get_genderized_person
from .functions.get_citations_from_string import get_syntactic_quotes
from .functions.assign_people_to_citations import assign_people_to_citations
from .utils.adapter import get_analyzed_article


DEFAULT_LOG_LEVEL = WARNING
LOG_FORMAT = "%(asctime)s [%(levelname)s]: %(message)s in %(pathname)s:%(lineno)d"


def get_log_level() -> int:
    """
    Gets the log level from the defined environment variable
    GGT_LOG_LEVEL or the default value if not found
    """
    try:
        env_var = environ["GGT_LOG_LEVEL"]
        return int(getLevelName(env_var))
    except KeyError:
        return DEFAULT_LOG_LEVEL


def _configure_root_logger() -> None:
    log_level = get_log_level()

    basicConfig()
    getLogger().setLevel(log_level)
    file_handler = FileHandler("run.log", mode="w", encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(Formatter(LOG_FORMAT))
    getLogger().addHandler(file_handler)


def _analyze_article(processor_nr: int) -> None:
    log.info("Starting processor %d", processor_nr)
    while True:
        try:
            article_dict = articles_queue.get(
                timeout=600
            )  # 10min, in case of network issues
            if article_dict["_id"] in analyzed_articles:
                log.debug(
                    "Skipping article with title '%s' (article id: %s)",
                    article_dict["title"],
                    article_dict["_id"],
                )
                continue
            start = datetime.now()
            log.debug("Trying to build article object from MongoDB result...")
            builder = ArticleBuilder()
            article = builder.from_db_result(article_dict).build()

            log.debug(
                "Successfully built article object for id %s (title: '%s')",
                article["_id"],
                article["title"],
            )
            log.info("Starting to analyze article with id %s...", article["_id"])

            log.debug(
                "Getting genderized person for article author '%s' (article id: %s)...",
                article["author"],
                article["_id"],
            )
            genderized_author = get_genderized_person(
                get_person_from_string(article["author"])
            )
            log.debug(
                "Successfully got genderized person for '%s'. Is of gender '%s' (article id: '%s')"
            )

            log.debug(
                "Starting analysis of article text (article id: %s)...", article["_id"]
            )
            article_text = article["text"]

            log.debug("Getting people from string (article id: %s)...", article["_id"])
            people = get_people_from_string(article_text)
            log.debug(
                "Successfully got people from string (article id: %s)", article["_id"]
            )

            log.debug(
                "Getting gender for extracted people (article id: %s)...",
                article["_id"],
            )
            genderized_people = map(get_genderized_person, people)
            log.debug(
                "Successfully extracted genders of extracted people (article id: %s)",
                article["_id"],
            )

            log.debug("Getting syntactic quotes (article id: %s)...", article["_id"])
            citations = get_syntactic_quotes(article_text)
            log.debug(
                "Successfully got syntactic quotes (article id: %s)", article["_id"]
            )

            log.debug(
                "Assigning people to citations (article id: %s)...", article["_id"]
            )
            citations_with_person = assign_people_to_citations(
                genderized_people, citations
            )
            log.debug(
                "Successfully assigned people to citations (article id: %s)",
                article["_id"],
            )

            log.info(
                "Successfully finished analyzing article with id %s (title: '%s')",
                article["_id"],
                article["title"],
            )
            log.debug(
                "Building article to insert into DB... (article id: %s)", article["_id"]
            )
            analyzed_article = get_analyzed_article(
                article, genderized_author, citations_with_person
            )
            log.debug(
                "Successfully build article to insert into DB! (article id: %s)",
                article["_id"],
            )

            log.debug(
                "Insert analyzed article into DB... (article id: %s)", article["_id"]
            )
            insert_analyzed_article(analyzed_article)
            log.info(
                "Successfully inserted analyzed article into DB! (article id: %s)",
                article["_id"],
            )

            log.debug(
                "Found %d citations within article with id %s",
                len(citations_with_person),
                article["_id"],
            )

            time_diff = datetime.now() - start
            log.info(
                "Analysis of article took %f seconds (article id: %s)",
                time_diff.total_seconds(),
                article["_id"],
            )
        except Empty:
            log.info("Queue is empty! Terminating processor %d!", processor_nr)
            return

_configure_root_logger()


articles_queue = Queue() # type: ignore


def __enqueue_articles(articles_cursor: Iterable[Dict[str, Any]]) -> None:
    log.debug("Writing articles from DB cursor into queue...")
    for article in articles_cursor:
        articles_queue.put(article)
    log.info(
        "Successfully filled multiprocessing queue with all articles. Queue size: %d",
        articles_queue.qsize(),
    )


log.debug("Trying to get cursor to articles from DB to analyze...")
cursor_process = Process(target=lambda: get_articles(__enqueue_articles))
cursor_process.start()


log.debug("Getting analyzed ids...")
ids = get_analyzed_article_ids()
analyzed_articles = set(map(lambda x: x["_id"], ids))
log.info("Starting of with %d analyzed articles!", len(analyzed_articles))


def __error_callback(exception: Exception) -> None:
    log.exception(exception, exception)
    pool.terminate()
    sys.exit(1)


# The part with the signal ensures that the child processes get terminated
# when the parent process is killed.
# Many thanks to Maxim Egorushkin @ https://stackoverflow.com/questions/11312525/catch-ctrlc-sigint-and-exit-multiprocesses-gracefully-in-python # pylint: disable=line-too-long
original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
poolsize = cpu_count()
with get_pool(poolsize) as pool:
    signal.signal(signal.SIGINT, original_sigint_handler)
    try:
        log.info("Starting to map articles from queue to analyze function...")
        res = pool.map_async(
            _analyze_article, range(poolsize), error_callback=__error_callback  # type: ignore
        )
        log.info("Successfully mapped articles from queue to analyze function!")
        log.info("Waiting for process pool termination...")
        res.wait()
    except KeyboardInterrupt:
        log.warning("Caught KeyboardInterrupt, terminating workers...")
        pool.terminate()
        cursor_process.join()
    except Exception as exc:
        log.exception("Unexpected exception '%s' occurred! Terminating workers...", exc)
        pool.terminate()
        cursor_process.join()
    else:
        print("Normal termination")
        pool.close()
        pool.join()
    cursor_process.close()
