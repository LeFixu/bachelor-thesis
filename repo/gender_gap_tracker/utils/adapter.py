"""Converters between types"""
from typing import Iterable
from uuid import uuid1
from ..classes.genderized_person import GenderizedPerson, Gender as LocalGender
from ..classes.citation_with_person import CitationWithPerson
from .db_driver.article import (
    AnalyzedArticle,
    Gender,
    ArticleWithGenderizedAuthor,
    Article,
    Quote,
    Person,
)


def __get_person_designation(person: GenderizedPerson) -> str:
    if len(person.substitute_nouns) > 0:
        substitute_nouns_list = ', '.join(person.substitute_nouns)
    else:
        substitute_nouns_list= ''

    return f"{person.first_name} {person.last_name}{substitute_nouns_list}"


def __get_gender_from_genderized_person(person: GenderizedPerson) -> Gender:
    if person.gender == LocalGender.FEMALE:
        return Gender.FEMALE
    if person.gender == LocalGender.MALE:
        return Gender.MALE
    return Gender.UNDEFINED


def __get_person_from_genderized_person(person: GenderizedPerson) -> Person:
    return Person(
        designation=__get_person_designation(person),
        gender=__get_gender_from_genderized_person(person),
    )


def __get_quote_from_genderized_quote(quote: CitationWithPerson) -> Quote:
    return Quote(
        subject=__get_person_from_genderized_person(quote.person),
        quotation_verb=quote.citation.citation_verb,
        quote=quote.citation.citation,
        start_of_quote_in_text=quote.citation.position_in_text[0],
    )


def get_analyzed_article(
    article: Article, author: GenderizedPerson, quotes: Iterable[CitationWithPerson]
) -> AnalyzedArticle:
    """Assembles an AnalyzedArticle Object"""
    return AnalyzedArticle(
        _id=uuid1().hex,
        article=ArticleWithGenderizedAuthor(
            _id=article["_id"],
            title=article["title"],
            lead=article["lead"],
            author=__get_person_from_genderized_person(author),
            source=article["source"],
            url=article["url"],
            published=article["published"],
            updated=article["updated"],
            text=article["text"],
        ),
        quotes=list(map(__get_quote_from_genderized_quote, quotes)),
    )
