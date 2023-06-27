"""Citation Person Module"""

from dataclasses import dataclass
from gender_gap_tracker.classes.genderized_person import GenderizedPerson
from gender_gap_tracker.classes.citation import Quote


@dataclass
class CitationWithPerson:
    """CitationWithPerson Class"""

    person: GenderizedPerson
    citation: Quote
    matching_probability: float

    def __init__(
        self,
        citation: Quote,
        person: GenderizedPerson,
        matching_probability: float,
    ) -> None:
        self.citation = citation
        self.person = person
        self.matching_probability = matching_probability
