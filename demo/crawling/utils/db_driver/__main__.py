"""This module provides a demonstration on how to use the db_driver"""

import logging
from time import time

from .article import Article, ArticleBuilder
from .db_driver import insert_article, insert_articles, print_top_n_articles


def _get_article() -> Article:
    return (
        ArticleBuilder()
        .with_title("Title")
        .with_lead("Lead")
        .with_url("Link")
        .with_published(round(time()))
        .with_paragraphs(["Paragraph 1", "Paragraph 2", "Paragraph 3"])
        .build()
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.info("STARTING MAIN")
    ITERATIONS = 100
    articles = [_get_article() for x in range(ITERATIONS)]

    start_time = time()
    for article in articles:
        insert_article(article)
    end_time = time()

    duration = end_time - start_time

    logging.info("Single inserts: Execution time: %s", duration)
    logging.info(
        "Single inserts: Mean execution time per insert: %s", {duration / ITERATIONS}
    )

    articles = [_get_article() for x in range(ITERATIONS)]
    start_time = time()
    insert_articles(articles)
    end_time = time()

    duration = end_time - start_time

    logging.info("Bulk inserts: Execution time: %s", duration)
    logging.info(
        "Bulk inserts: Mean execution time per insert: %s", {duration / ITERATIONS}
    )

    print_top_n_articles(20)
