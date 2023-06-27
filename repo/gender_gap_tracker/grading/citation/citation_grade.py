from statistics import mean
from typing import List
from dataclasses import dataclass


@dataclass
class CitationGrade:
    citation_id: int
    subject_grade: float
    citation_grade: float
    verb_grade: float

    def __init__(
        self,
        citation_id: int,
        subject_grade: float,
        citation_grade: float,
        verb_grade: float,
    ) -> None:
        self.citation_id = citation_id
        self.subject_grade = subject_grade
        self.citation_grade = citation_grade
        self.verb_grade = verb_grade

    @property
    def final_grade(self) -> float:
        return mean([self.subject_grade, self.citation_grade, self.verb_grade])

    def __dict__(self):
        return {
            "citation_id": self.citation_id,
            "subject_grade": self.subject_grade,
            "citation_grade": self.citation_grade,
            "verb_grade": self.verb_grade,
            "final_grade": self.final_grade,
        }


@dataclass
class ArticleGrade:
    article_id: int
    citations_found: int
    citations_count: int
    citation_grades: List[CitationGrade]

    def __init__(
        self,
        article_id: int,
        citations_found: int,
        citations_count: int,
        citation_grades: List[CitationGrade],
    ) -> None:
        self.article_id = article_id
        self.citations_found = citations_found
        self.citations_count = citations_count
        self.citation_grades = citation_grades

    @property
    def recall(self) -> float:
        return self.citations_found / self.citations_count

    @property
    def quality_grade(self) -> float:
        if len(self.citation_grades) < 1:
            return 0.0
        return mean([x.final_grade for x in self.citation_grades])

    def __dict__(self):
        return {
            "article_id": self.article_id,
            "citations_found": self.citations_found,
            "citations_count": self.citations_count,
            "recall": self.recall,
            "quality_grade": self.quality_grade,
            "citation_grades": [x.__dict__() for x in self.citation_grades],
        }


@dataclass
class PortalGrade:
    portal: str
    article_grades: List[ArticleGrade]

    def __init__(self, portal: str, article_grades: List[ArticleGrade]) -> None:
        self.portal = portal
        self.article_grades = article_grades

    @property
    def citations_found(self) -> int:
        return sum(map(lambda x: x.citations_found, self.article_grades))

    @property
    def citations_count(self) -> int:
        return sum(map(lambda x: x.citations_count, self.article_grades))

    @property
    def recall(self) -> float:
        return self.citations_found / self.citations_count

    @property
    def quality_grade(self) -> float:
        if len(self.article_grades) < 1:
            return 0.0
        return mean(map(lambda x: x.quality_grade, self.article_grades))

    def __dict__(self):
        return {
            "portal": self.portal,
            "citations_found": self.citations_found,
            "citations_count": self.citations_count,
            "recall": self.recall,
            "quality_grade": self.quality_grade,
            "article_grades": [x.__dict__() for x in self.article_grades],
        }


@dataclass
class QuotationExtractionGrade:
    quotation_type: str
    article_grades: List[PortalGrade]

    def __init__(self, portal: str, portal_grades: List[PortalGrade]) -> None:
        self.quotation_type = portal
        self.portal_grades = portal_grades

    @property
    def citations_found(self) -> int:
        return sum(map(lambda x: x.citations_found, self.portal_grades))

    @property
    def citations_count(self) -> int:
        return sum(map(lambda x: x.citations_count, self.portal_grades))

    @property
    def recall(self) -> float:
        if len(self.portal_grades) < 1:
            return 0.0
        return mean(map(lambda x: x.recall, self.portal_grades))

    @property
    def quality_grade(self) -> float:
        if len(self.portal_grades) < 1:
            return 0.0
        return mean(map(lambda x: x.quality_grade, self.portal_grades))

    def __dict__(self):
        return {
            "quotation_type": self.quotation_type,
            "citations_found": self.citations_found,
            "citations_count": self.citations_count,
            "recall": self.recall,
            "quality_grade": self.quality_grade,
            "portal_grades": [x.__dict__() for x in self.portal_grades],
        }
