import os
import json
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from statistics import mean
from difflib import SequenceMatcher
from gender_gap_tracker.classes.person import Person
from gender_gap_tracker.grading.people.person_grade import (
    PersonGrade,
    ArticleGrade,
    PortalGrade,
    PeopleExtractionGrade,
)
from gender_gap_tracker.functions.get_people_from_string import get_people_from_string
import spacy

nlp = spacy.load("de_core_news_lg")


def __get_string_similarity(a: str, b: str) -> float:
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
    return SequenceMatcher(None, a, b).ratio()


def __get_str_list_similarity(list1: List[str], list2: List[str]) -> float:
    if len(list1) == 0 and len(list2) == 0:
        return 1.0
    if len(list1) == 0 or len(list2) == 0:
        return 0.0

    # Konvertiere alle Strings in den Listen in Kleinbuchstaben
    list1 = [s.lower() for s in list1]
    list2 = [s.lower() for s in list2]

    vec1 = nlp(" ".join(list1)).vector
    vec2 = nlp(" ".join(list2)).vector
    vec1_norm = vec1 / (vec1.dot(vec1) ** 0.5)
    vec2_norm = vec2 / (vec2.dot(vec2) ** 0.5)
    similarity = vec1_norm.dot(vec2_norm)
    set1 = set(list1)
    set2 = set(list2)
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    jaccard_similarity = len(intersection) / len(union)
    overall_similarity = (similarity + jaccard_similarity) / 2
    if overall_similarity < 0:
        return 0.0
    return overall_similarity


def __get_sequence_similarity(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    """Calculate the amount of overlap between two tuples of integers

    >>> __get_sequence_similarity((0,1), (1, 2))
    0.0
    >>> __get_sequence_similarity((0,1), (4, 6))
    0.0
    >>> __get_sequence_similarity((3, 5), (2, 3))
    0.0
    >>> __get_sequence_similarity((4, 5), (2, 3))
    0.0
    >>> __get_sequence_similarity((2, 4), (2, 4))
    1.0
    >>> __get_sequence_similarity((1, 3), (2, 4))
    0.5
    >>> __get_sequence_similarity((2, 4), (1, 3))
    0.5
    >>> __get_sequence_similarity((2, 4), (2, 3))
    0.75
    >>> __get_sequence_similarity((2, 3), (2, 4))
    0.75
    """

    # No overlap
    if a[0] >= b[1]:
        return 0.0
    if b[0] >= a[1]:
        return 0.0

    def get_tuple_span(t: Tuple[int, int]) -> float:
        return float(t[1] - t[0])

    overlap_a = overlap_b = 0.0
    # Sequence of b is within a
    if a[0] <= b[0] and a[1] >= b[1]:
        overlap_a = get_tuple_span(b) / get_tuple_span(a)
        overlap_b = 1
    # sequence of a is within b
    elif b[0] <= a[0] and b[1] >= a[1]:
        overlap_a = 1
        overlap_b = get_tuple_span(a) / get_tuple_span(b)
    # a and b are overlapping, but a is first
    elif a[0] <= b[0] and a[1] <= b[1]:
        overlap_a = (a[1] - b[0]) / get_tuple_span(a)
        overlap_b = (a[1] - b[0]) / get_tuple_span(b)
    # a and b are overlapping, but b is first
    elif b[0] <= a[0] and b[1] <= a[1]:
        overlap_a = (b[1] - a[0]) / get_tuple_span(a)
        overlap_b = (b[1] - a[0]) / get_tuple_span(b)
    # exact match
    else:
        return 1.0

    return mean([overlap_a, overlap_b])


def __get_nearest_person(
    person_location_start: int, people_to_choose_from: List[Person]
) -> Optional[Person]:
    if len(people_to_choose_from) == 0:
        return None
    return min(
        people_to_choose_from,
        key=lambda c: abs(person_location_start - c.positions_in_text[0]),
    )


def __get_grade_for_person(calculated: Person, solution: Person) -> PersonGrade:
    if solution is None and calculated is None:
        return PersonGrade(1, 1.0, 1.0)
    if solution is None and calculated is not None:
        return PersonGrade(1, 0.0, 0.0)

    return PersonGrade(
        calculated.positions_in_text[0],
        __get_string_similarity(calculated.first_name, solution.first_name),
        __get_string_similarity(calculated.last_name, solution.last_name),
    )


def __grade_article(
    article_id: int, article_text: str, expected_people: List[Person]
) -> ArticleGrade:

    people = get_people_from_string(article_text)

    def get_grade_for_person(p: Person) -> PersonGrade:
        solution = __get_nearest_person(p.positions_in_text[0], expected_people)
        print(f"found person: {p}")
        return __get_grade_for_person(p, solution)

    people_grades = list(map(lambda p: get_grade_for_person(p), people))
    return ArticleGrade(article_id, len(people), len(expected_people), people_grades)


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
) -> List[Tuple[int, str, List[Person]]]:
    article_texts = {}
    people = {}
    nrs = set()

    grading_data = os.listdir(source_dir)
    for file_name in grading_data:
        try:
            parts = file_name.split(".")
            nr = parts[0]
            type_ = parts[1]
            nrs.add(nr)

            with open(source_dir / file_name, "r", encoding="utf8") as f:
                if type_ == "article":
                    article_texts[nr] = f.read()
                elif type_ == "people":
                    people[nr] = __get_people_from_json(json.load(f))

        except IndexError as e:
            print(f"Unexpected {e} for file '{file_name}'. Continuing...")
        except json.decoder.JSONDecodeError as e:
            print(f"Malformed JSON! Skipping '{file_name}'...")

    retVal = []
    for nr in nrs:
        try:
            retVal.append((int(nr), article_texts[nr], people[nr]))
        except IndexError as e:
            print(f"Either article or citations not found for case {nr}!")

    return retVal


def __get_sources_dir() -> Path:
    # path = "/".join(os.path.realpath(__file__).split("/")[:-1])
    # cur_dir = Path(path)
    cur_dir = "./gender_gap_tracker/grading/people/"
    return Path(cur_dir + "grading_data")


def __get_grade_for_source(source: str) -> PortalGrade:
    source_dir = __get_sources_dir() / source
    article_people_tuples = __get_grading_material_for_source(source_dir)
    grades = list(
        map(lambda t: __grade_article(t[0], t[1], t[2]), article_people_tuples)
    )

    return PortalGrade(source, grades)


def get_grades_by_source() -> Dict:
    sources_dir = __get_sources_dir()
    sources = os.listdir(sources_dir)

    grades_by_source = list(map(lambda source: __get_grade_for_source(source), sources))
    return PeopleExtractionGrade("normal", grades_by_source).__dict__()


if __name__ == "__main__":
    import doctest

    doctest.testmod()
