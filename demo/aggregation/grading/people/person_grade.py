from statistics import mean
from typing import List
from dataclasses import dataclass
from json import dumps
from functools import reduce


@dataclass
class PersonGrade:
    person_id: int
    first_name_grade: float
    last_name_grade: float

    def __init__(
        self, person_id: int, first_name_grade: float, last_name_grade: float
    ) -> None:
        self.person_id = person_id
        self.first_name_grade = first_name_grade
        self.last_name_grade = last_name_grade

    @property
    def final_grade(self) -> float:
        return mean([self.first_name_grade, self.last_name_grade])

    def __dict__(self):
        return {
            "person_id": self.person_id,
            "first_name_grade": self.first_name_grade,
            "last_name_grade": self.last_name_grade,
            "final_grade": self.final_grade,
        }


@dataclass
class ArticleGrade:
    article_id: int
    people_found: int
    people_count: int
    people_grades: List[PersonGrade]

    def __init__(
        self,
        article_id: int,
        people_found: int,
        people_count: int,
        people_grades: List[PersonGrade],
    ) -> None:
        self.article_id = article_id
        self.people_found = people_found
        self.people_count = people_count
        self.people_grades = people_grades

    @property
    def recall(self) -> float:
        if self.people_found == 0 and self.people_count == 0:
            return 1.0
        if self.people_count == 0:
            return 0.0
        return self.people_found / self.people_count

    @property
    def quality_grade(self) -> float:
        if len(self.people_grades) < 1:
            return 0.0
        return mean([x.final_grade for x in self.people_grades])

    def __dict__(self):
        return {
            "article_id": self.article_id,
            "people_found": self.people_found,
            "people_count": self.people_count,
            "recall": self.recall,
            "quality_grade": self.quality_grade,
            "people_grades": [x.__dict__() for x in self.people_grades],
        }


@dataclass
class PortalGrade:
    portal: str
    article_grades: List[ArticleGrade]

    def __init__(self, portal: str, article_grades: List[ArticleGrade]) -> None:
        self.portal = portal
        self.article_grades = article_grades

    @property
    def people_found(self) -> int:
        return sum(map(lambda x: x.people_found, self.article_grades))

    @property
    def people_count(self) -> int:
        return sum(map(lambda x: x.people_count, self.article_grades))

    @property
    def recall(self) -> float:
        if len(self.article_grades) < 1:
            return 0.0
        return mean(map(lambda x: x.recall, self.article_grades))

    @property
    def quality_grade(self) -> float:
        if len(self.article_grades) < 1:
            return 0.0
        return mean(map(lambda x: x.quality_grade, self.article_grades))

    def __dict__(self):
        return {
            "portal": self.portal,
            "people_found": self.people_found,
            "people_count": self.people_count,
            "recall": self.recall,
            "quality_grade": self.quality_grade,
            "article_grades": [x.__dict__() for x in self.article_grades],
        }


@dataclass
class PeopleExtractionGrade:
    people_type: str
    article_grades: List[PortalGrade]

    def __init__(self, portal: str, portal_grades: List[PortalGrade]) -> None:
        self.people_type = portal
        self.portal_grades = portal_grades

    @property
    def people_found(self) -> int:
        return sum(map(lambda x: x.people_found, self.portal_grades))

    @property
    def people_count(self) -> int:
        return sum(map(lambda x: x.people_count, self.portal_grades))

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
            "people_type": self.people_type,
            "people_found": self.people_found,
            "people_count": self.people_count,
            "recall": self.recall,
            "quality_grade": self.quality_grade,
            "portal_grades": [x.__dict__() for x in self.portal_grades],
        }
