import os
import json
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from statistics import mean
from ....utils.string_similarity import get_string_similarity
from ....classes.citation import Quote
from ..citation_grade import (
    CitationGrade,
    ArticleGrade,
    PortalGrade,
    QuotationExtractionGrade,
)
from ....functions.get_citations_from_string import get_syntactic_quotes

__CITATION_IDENTIFIED_QUALITY_THREASHOLD = 0.5


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


def __get_nearest_citation(
    citation_location_start: int, citations_to_choose_from: List[Quote]
) -> Quote:
    return min(
        citations_to_choose_from,
        key=lambda c: abs(citation_location_start - c.position_in_text[0]),
    )


def __get_grade_for_citation(calculated: Quote, solution: Quote) -> CitationGrade:
    return CitationGrade(
        calculated.position_in_text[0],
        get_string_similarity(calculated.subject, solution.subject),
        get_string_similarity(calculated.citation, solution.citation),
        get_string_similarity(calculated.citation_verb, solution.citation_verb),
    )


def __grade_article(
    article_id: int, article_text: str, expected_citations: List[Quote]
) -> ArticleGrade:

    citations = get_syntactic_quotes(article_text)

    def get_grade_for_citation(c: Quote) -> CitationGrade:
        solution = __get_nearest_citation(c.position_in_text[0], expected_citations)
        return __get_grade_for_citation(c, solution)

    citation_grades = list(map(lambda c: get_grade_for_citation(c), citations))
    citations_found_with_sufficient_quality = list(
        filter(
            lambda c: c.final_grade >= __CITATION_IDENTIFIED_QUALITY_THREASHOLD,
            citation_grades,
        )
    )
    return ArticleGrade(
        article_id,
        len(citations_found_with_sufficient_quality),
        len(expected_citations),
        citation_grades,
    )


def __get_citations_from_json(json_array: List[Dict]) -> List[Quote]:
    def get_citation_from_json(json_obj: Dict) -> Optional[Quote]:
        try:
            return Quote(
                json_obj["position_in_text"],
                json_obj["citation"],
                json_obj["subject"],
                json_obj["citation_verb"],
            )
        except IndexError as e:
            print(f"Error reading value from JSON (IndexError)! '{e}'")
            print(f"Skipping...")
            return None

    return list(filter(lambda x: x is not None, map(get_citation_from_json, json_array)))  # type: ignore


def __get_grading_material_for_source(
    source_dir: Path,
) -> List[Tuple[int, str, List[Quote]]]:
    article_texts = {}
    citations = {}
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
                elif type_ == "citations":
                    citations[nr] = __get_citations_from_json(json.load(f))

        except IndexError as e:
            print(f"Unexpected {e} for file '{file_name}'. Continuing...")
        except json.decoder.JSONDecodeError as e:
            print(f"Malformed JSON! Skipping '{file_name}'...")

    retVal = []
    for nr in nrs:
        try:
            retVal.append((int(nr), article_texts[nr], citations[nr]))
        except IndexError as e:
            print(f"Either article or citations not found for case {nr}!")

    return retVal


def __get_sources_dir() -> Path:
    path = "/".join(os.path.realpath(__file__).split("/")[:-1])
    cur_dir = Path(path)
    return cur_dir / "grading_data"


def __get_grade_for_source(source: str) -> PortalGrade:
    source_dir = __get_sources_dir() / source
    article_citations_tuples = __get_grading_material_for_source(source_dir)
    grades = list(
        map(lambda t: __grade_article(t[0], t[1], t[2]), article_citations_tuples)
    )

    return PortalGrade(source, grades)


def get_grades_by_source() -> Dict:
    sources_dir = __get_sources_dir()
    sources = os.listdir(sources_dir)

    grades_by_source = list(map(lambda source: __get_grade_for_source(source), sources))
    return QuotationExtractionGrade("syntactic", grades_by_source).__dict__()


if __name__ == "__main__":
    import doctest

    doctest.testmod()
