"""Person Module"""

from dataclasses import dataclass


@dataclass
class Person:
    """Person Class"""

    first_name: str
    last_name: str
    salutation: list[str]  # Herr, Frau, Doktor, Prof.
    pronouns_and_articles: list[
        str
    ]  # er, sie, thei, ihr, ihre, sein, seine # der, die, das
    substitute_nouns: list[
        str
    ]  # Informatikerin, Studentin, Schwester, Tochter, Prinz, Experte
    positions_in_text: list[int]  # mittelwert ((start+end)/2) von index in text
