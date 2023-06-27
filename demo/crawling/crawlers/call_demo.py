"""Demonstrate imports"""

# from article import ArticleBuilder
from ..utils.db_driver.__main__ import _get_article

# print(ArticleBuilder().build())
article = _get_article()


def a_function() -> None:
    """Test function"""
    print(article)


if __name__ == "__main__":
    a_function()
