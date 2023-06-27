from statistics import mean
from typing import List
from dataclasses import dataclass
from json import dumps
from functools import reduce


@dataclass
class GenderizedPersonGrade:
    person_id: int
    gender_grade: float

    def __init__(self, person_id: int, gender_grade: float) -> None:
        self.person_id = person_id
        self.gender_grade = gender_grade

    @property
    def final_grade(self) -> float:
        return self.gender_grade

    def __dict__(self):
        return {"person_id": self.person_id, "gender_grade": self.gender_grade}


@dataclass
class ArticleGrade:
    article_id: int
    gender_found: int
    gender_count: int
    gender_grades: List[GenderizedPersonGrade]

    def __init__(
        self,
        article_id: int,
        gender_found: int,
        gender_count: int,
        genderized_people_grades: List[GenderizedPersonGrade],
    ) -> None:
        self.article_id = article_id
        self.gender_found = gender_found
        self.gender_count = gender_count
        self.genderized_people_grades = genderized_people_grades

    @property
    def recall(self) -> float:
        return self.gender_found / self.gender_count

    @property
    def quality_grade(self) -> float:
        if len(self.genderized_people_grades) < 1:
            return 0.0
        return mean([x.final_grade for x in self.genderized_people_grades])

    def __dict__(self):
        return {
            "article_id": self.article_id,
            "gender_found": self.gender_found,
            "gender_count": self.gender_count,
            "recall": self.recall,
            "quality_grade": self.quality_grade,
            "genderized_people_grades": [
                x.__dict__() for x in self.genderized_people_grades
            ],
        }


@dataclass
class PortalGrade:
    portal: str
    article_grades: List[ArticleGrade]

    def __init__(self, portal: str, article_grades: List[ArticleGrade]) -> None:
        self.portal = portal
        self.article_grades = article_grades

    @property
    def gender_found(self) -> int:
        return sum(map(lambda x: x.gender_found, self.article_grades))

    @property
    def gender_count(self) -> int:
        return sum(map(lambda x: x.gender_count, self.article_grades))

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
            "gender_found": self.gender_found,
            "gender_count": self.gender_count,
            "recall": self.recall,
            "quality_grade": self.quality_grade,
            "article_grades": [x.__dict__() for x in self.article_grades],
        }


@dataclass
class GenderExtractionGrade:
    people_type: str
    article_grades: List[PortalGrade]

    def __init__(self, portal: str, portal_grades: List[PortalGrade]) -> None:
        self.people_type = portal
        self.portal_grades = portal_grades

    @property
    def gender_found(self) -> int:
        return sum(map(lambda x: x.gender_found, self.portal_grades))

    @property
    def gender_count(self) -> int:
        return sum(map(lambda x: x.gender_count, self.portal_grades))

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
            "gender_found": self.gender_found,
            "gender_count": self.gender_count,
            "recall": self.recall,
            "quality_grade": self.quality_grade,
            "portal_grades": [x.__dict__() for x in self.portal_grades],
        }
