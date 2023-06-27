"""Article Module"""

from dataclasses import dataclass
from gender_gap_tracker.classes.citation_with_person import CitationWithPerson


@dataclass
class Article:
    """Article Class"""

    url: str
    source: str  # Portal
    citations_with_person: list[CitationWithPerson]
