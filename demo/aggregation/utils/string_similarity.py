"""This module provides functionality to compare strings"""

from difflib import SequenceMatcher


def get_string_similarity(string_1: str, string_2: str) -> float:
    """Calculate the character based string similarity of two strings

    >>> __get_string_similarity("Apple", "Apple")
    1.0
    >>> __get_string_similarity("Apple", "Appl")
    0.8888888888888888
    >>> __get_string_similarity("Appl", "Apple")
    0.8888888888888888
    >>> __get_string_similarity("Apple", "Pare")
    0.2222222222222222
    """
    return SequenceMatcher(None, string_1, string_2).ratio()
