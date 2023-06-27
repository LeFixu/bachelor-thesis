"""This module provides data structures that can be used to insert data into the mongoDB"""

from __future__ import annotations
from enum import Enum
from typing import List, Optional, TypedDict, Dict, Any
from uuid import uuid1
from hashlib import sha1
from functools import reduce


class Person(TypedDict):
    """Class representing a person"""
    designation: str
    gender: Gender


class Article(TypedDict):
    """This class represents a mongoDB article document"""

    _id: str
    title: str
    lead: str
    url: str
    author: str
    source: str
    published: int
    updated: Optional[int]
    text: str
    paragraph_hashes: List[str]


class Gender(Enum):
    """The defined genders"""
    UNDEFINED = "undefined"
    FEMALE = "female"
    MALE = "male"


class Quote(TypedDict):
    """Syntactic Quote"""
    subject: Person
    quotation_verb: str
    quote: str
    start_of_quote_in_text: int


class ArticleWithGenderizedAuthor(TypedDict):
    """Article with Person instead of string as author"""
    _id: str
    title: str
    lead: str
    url: str
    author: Person
    source: str
    published: int
    updated: Optional[int]
    text: str


class AnalyzedArticle(TypedDict):
    """Represents an article and its extracted citations"""

    _id: str
    article: ArticleWithGenderizedAuthor
    quotes: List[Quote]


class ArticleBuilder:
    """This builder class aims at simplifying the creation of article objects"""

    _id: str
    title: str
    lead: str
    url: str
    author: str
    source: str
    published: int
    updated: Optional[int]
    text: str
    paragraph_hashes: List[str]

    def __init__(self) -> None:
        """Initialize the builder"""
        self._id = uuid1().hex
        self.title = ""
        self.lead = ""
        self.url = ""
        self.author = ""
        self.source = ""
        self.published = 0
        self.updated = None
        self.text = ""
        self.paragraph_hashes = []

    def from_db_result(self, db_result: Dict[str, Any]) -> ArticleBuilder:
        """Build an article from a dict coming from the mongoDB"""
        self._id = db_result["_id"]
        self.title = db_result["title"]
        self.lead = db_result["lead"]
        self.url = db_result["url"]
        self.author = db_result["author"]
        self.published = db_result["published"]
        self.updated = db_result["updated"]
        self.text = db_result["text"]
        self.source = db_result["source"]
        self.paragraph_hashes = db_result["paragraph_hashes"]
        return self

    def with_id(self, id_: str) -> ArticleBuilder:
        """Define the id"""
        self._id = id_
        return self

    def with_title(self, title: str) -> ArticleBuilder:
        """Define the title"""
        self.title = title
        return self

    def with_lead(self, lead: str) -> ArticleBuilder:
        """Define the lead"""
        self.lead = lead
        return self

    def with_url(self, url: str) -> ArticleBuilder:
        """Define the link"""
        self.url = url
        return self

    def with_author(self, author: str) -> ArticleBuilder:
        """Define the author"""
        self.author = author
        return self

    def with_source(self, source: str) -> ArticleBuilder:
        """Define the author"""
        self.source = source
        return self

    def with_published(self, published: int) -> ArticleBuilder:
        """Define the published timestamp"""
        self.published = published
        return self

    def with_updated(self, updated: int) -> ArticleBuilder:
        """Define the updated timestamp"""
        self.updated = updated
        return self

    def with_text(self, text: str) -> ArticleBuilder:
        """Define the text"""
        self.text = text
        return self

    def with_paragraphs(self, paragraphs: List[str]) -> ArticleBuilder:
        """Define the text and the paragraph hashes"""
        self.text = reduce(lambda a, b: a + " " + b, paragraphs)
        self.paragraph_hashes = self._get_hashes_for_strings(paragraphs)
        return self

    def build(self) -> Article:
        """Build the article object"""
        return {
            "_id": self._id,
            "title": self.title,
            "lead": self.lead,
            "url": self.url,
            "author": self.author,
            "source": self.source,
            "published": self.published,
            "updated": self.updated,
            "text": self.text,
            "paragraph_hashes": self.paragraph_hashes,
        }

    def _get_hashes_for_strings(self, strings: List[str]) -> List[str]:
        encoded = map(lambda a: a.encode("utf-8"), strings)
        hashed = map(sha1, encoded)
        stringified = map(lambda a: a.hexdigest(), hashed)
        return list(stringified)
