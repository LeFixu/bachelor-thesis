"""This module provides data structures that can be used to insert data into the mongoDB"""


from __future__ import annotations
from typing import TypedDict
from uuid import uuid1


class Url(TypedDict):
    """This class represents a mongoDB url document"""

    _id: str
    url: str
    source: str


class UrlBuilder:
    """This builder class aims at simplifying the creation of url objects"""

    _id: str
    url: str
    source: str

    def __init__(self) -> None:
        """Initialize the builder"""
        self._id = uuid1().hex
        self.url = ""

    def with_id(self, id_: str) -> UrlBuilder:
        """Define the id"""
        self._id = id_
        return self

    def with_url(self, url: str) -> UrlBuilder:
        """Define the link"""
        self.url = url
        return self

    def with_source(self, source: str) -> UrlBuilder:
        """Define the link"""
        self.source = source
        return self

    def build(self) -> Url:
        """Build the url object"""
        return {"_id": self._id, "url": self.url, "source": self.source}
