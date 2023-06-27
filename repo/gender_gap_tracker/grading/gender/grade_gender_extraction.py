import os
import json
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from statistics import mean
from difflib import SequenceMatcher
from gender_gap_tracker.classes.genderized_person import GenderizedPerson, Gender
from gender_gap_tracker.classes.person import Person
from gender_gap_tracker.grading.gender.genderized_person_grade import (
    GenderizedPersonGrade,
    ArticleGrade,
    PortalGrade,
    GenderExtractionGrade,
)
from gender_gap_tracker.functions.get_genderized_person import get_genderized_person


def __get_gender_similarity(a: Gender, b: Gender) -> float:
    if a == b:
        return 1.0
    else:
        return 0.0


def __get_nearest_person(
    person_location_start: int, people_to_choose_from: List[Person]
) -> Person:
    for s in people_to_choose_from:
        if s.positions_in_text[0] == person_location_start:
            return s


def __get_grade_for_genderized_person(
    calculated: GenderizedPerson, solution: GenderizedPerson
) -> GenderizedPersonGrade:
    return GenderizedPersonGrade(
        calculated.positions_in_text[0],
        __get_gender_similarity(calculated.gender, solution.gender),
    )


def __grade_article(
    article_id: int,
    people: List[Person],
    expected_genderized_people: List[GenderizedPerson],
) -> ArticleGrade:

    genderized_people = list(map(lambda p: get_genderized_person(p), people))

    def get_grade_for_genderized_person(p: GenderizedPerson) -> GenderizedPersonGrade:
        solution = __get_nearest_person(
            p.positions_in_text[0], expected_genderized_people
        )
        print(f"found GenderizedPerson: {p}")
        return __get_grade_for_genderized_person(p, solution)

    genderized_people_grades = list(
        map(lambda p: get_grade_for_genderized_person(p), genderized_people)
    )
    return ArticleGrade(
        article_id,
        len(genderized_people),
        len(expected_genderized_people),
        genderized_people_grades,
    )


def __get_genderized_people_from_json(json_array: List[Dict]) -> List[GenderizedPerson]:
    def get_genderized_person_from_json(json_obj: Dict) -> Optional[GenderizedPerson]:
        try:
            return GenderizedPerson(
                json_obj["first_name"],
                json_obj["last_name"],
                json_obj["salutation"],
                json_obj["pronouns_and_articles"],
                json_obj["substitute_nouns"],
                json_obj["positions_in_text"],
                Gender[json_obj["gender"]],
                json_obj["probability"],
            )
        except IndexError as e:
            print(f"Error reading value from JSON (IndexError)! '{e}'")
            print(f"Skipping...")
            return None

    return list(filter(lambda x: x is not None, map(get_genderized_person_from_json, json_array)))  # type: ignore


def __get_people_from_json(json_array: List[Dict]) -> List[Person]:
    def get_person_from_json(json_obj: Dict) -> Optional[Person]:
        try:
            return Person(
                json_obj["first_name"],
                json_obj["last_name"],
                json_obj["salutation"],
                json_obj["pronouns_and_articles"],
                json_obj["substitute_nouns"],
                json_obj["positions_in_text"],
            )
        except IndexError as e:
            print(f"Error reading value from JSON (IndexError)! '{e}'")
            print(f"Skipping...")
            return None

    return list(filter(lambda x: x is not None, map(get_person_from_json, json_array)))  # type: ignore


def __get_grading_material_for_source(
    source_dir: Path,
) -> List[Tuple[int, List[Person], List[GenderizedPerson]]]:
    people = {}
    genderized_people = {}
    nrs = set()

    grading_data = os.listdir(source_dir)
    for file_name in grading_data:
        try:
            parts = file_name.split(".")
            nr = parts[0]
            type_ = parts[1]
            nrs.add(nr)

            with open(source_dir / file_name, "r", encoding="utf8") as f:
                if type_ == "people":
                    people[nr] = __get_people_from_json(json.load(f))
                elif type_ == "genderized_people":
                    genderized_people[nr] = __get_genderized_people_from_json(
                        json.load(f)
                    )

        except IndexError as e:
            print(f"Unexpected {e} for file '{file_name}'. Continuing...")
        except json.decoder.JSONDecodeError as e:
            print(f"Malformed JSON! Skipping '{file_name}'...")

    retVal = []
    for nr in nrs:
        try:
            retVal.append((int(nr), people[nr], genderized_people[nr]))
        except IndexError as e:
            print(f"Either people or genderized_people not found for case {nr}!")

    return retVal


def __get_sources_dir() -> Path:
    # path = "/".join(os.path.realpath(__file__).split("/")[:-1])
    # cur_dir = Path(path)
    cur_dir = "./gender_gap_tracker/grading/gender/"
    return Path(cur_dir + "grading_data")


def __get_grade_for_source(source: str) -> PortalGrade:
    source_dir = __get_sources_dir() / source
    people_genderized_people_tuples = __get_grading_material_for_source(source_dir)
    grades = list(
        map(
            lambda t: __grade_article(t[0], t[1], t[2]), people_genderized_people_tuples
        )
    )

    return PortalGrade(source, grades)


def get_grades_by_source() -> Dict:
    sources_dir = __get_sources_dir()
    sources = os.listdir(sources_dir)

    grades_by_source = list(map(lambda source: __get_grade_for_source(source), sources))
    return GenderExtractionGrade("normal", grades_by_source).__dict__()


if __name__ == "__main__":
    import doctest

    doctest.testmod()
