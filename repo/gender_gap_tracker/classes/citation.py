"""citation module"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class Quote:
    """Represents a citation / quote"""

    position_in_text: Tuple[int, int]
    citation: str
    subject: str  # der Bundesrat Berset
    citation_verb: str  # sagte, meinte, erklärte

    def __init__(
        self,
        position_in_text: int,
        citation: str,
        subject: str,
        citation_verb: str,
    ):
        self.position_in_text = (
            position_in_text + 1,
            position_in_text + 1 + len(citation),
        )
        self.citation = citation
        self.subject = subject
        self.citation_verb = citation_verb
