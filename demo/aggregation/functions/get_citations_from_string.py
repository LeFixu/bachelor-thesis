"""
This module can be used to extract citations from a string.
Currently only syntactic quotes included
"""

import os
from functools import reduce
from operator import iconcat
from typing import List, Optional, Callable, Tuple, TypeVar, Iterator
from nltk import Tree  # type: ignore
from spacy import load
from spacy.tokens import Doc, Token
from spacy.language import Language
from ..classes.citation import Quote


class _NotFoundError(BaseException):
    pass


__NLP: Optional[Language] = None  # cached spacy parser instance


def __get_nlp(model: str = "de_core_news_lg") -> Language:
    # pylint: disable=global-statement
    global __NLP
    # pylint: enable=global-statement
    if __NLP is None:
        __NLP = load(model)
    return __NLP


def __get_roots(string: str) -> Iterator[Token]:
    return (sent.root for sent in __get_nlp()(string).sents)


__QUOTATION_VERBS: Optional[List[str]] = None


def __get_quotation_verbs() -> List[str]:
    # pylint: disable=global-statement
    global __QUOTATION_VERBS
    # pylint: enable=global-statement

    if __QUOTATION_VERBS is not None:
        return __QUOTATION_VERBS

    cur_dir = "/".join(os.path.realpath(__file__).split("/")[:-1])
    with open(cur_dir + "/quotation_verbs.txt", "r", encoding="utf8") as file_pointer:
        quotation_verbs_raw = file_pointer.read()

    quotation_verbs_doc: Doc = __get_nlp()(quotation_verbs_raw)
    quotation_verbs = list(map(lambda t: t.lemma_, quotation_verbs_doc))

    __QUOTATION_VERBS = quotation_verbs
    return quotation_verbs


def __get_hilfsverben() -> List[str]:
    return ["sein", "haben"]


# Breadth First Search
def __get_nearest_tokens_by_condition(
    node: Token, condition: Callable[[Token], bool]
) -> List[Token]:
    def get_nearest_by(
        node: Token, condition: Callable[[Token], bool], depth: int
    ) -> List[Tuple[Token, int]]:
        # check current node
        if condition(node):
            return [(node, depth)]

        # Recursion step (flatten result)
        return __get_flattened_list(
            [get_nearest_by(n, condition, depth + 1) for n in node.children]
        )

    results = get_nearest_by(node, condition, 0)
    if len(results) < 1:
        return []
    min_depth = min(results, key=lambda t: t[1])[1]

    return list(map(lambda t: t[0], filter(lambda t: t[1] == min_depth, results)))


T = TypeVar("T")


def __get_flattened_list(list_of_lists: List[List[T]]) -> List[T]:
    return reduce(iconcat, list_of_lists, [])


def __get_flattened_tree(node: Token) -> List[Token]:
    def get_flattened_tree_(node: Token) -> List[Token]:
        return reduce(
            iconcat, [get_flattened_tree_(child) for child in node.children], [node]
        )

    return sorted(get_flattened_tree_(node), key=lambda x: x.i)


def __get_text_from_tree(node: Token) -> str:
    return "".join(map(lambda x: x.text_with_ws, __get_flattened_tree(node))).strip()


def __get_subject_node(node: Token) -> Token:
    condition = lambda n: n.dep_ == "sb"
    result = __get_nearest_tokens_by_condition(node, condition)
    if len(result) < 1:
        raise _NotFoundError()
    return result[0]


def __get_quote_node(root: Token) -> Token:
    result = []

    # Perfekt, Plusquamperfekt, Futur
    if root.lemma_ in __get_hilfsverben():
        condition = (
            lambda n: n.head.lemma_ in __get_quotation_verbs() and n.dep_ == "oc"
        )
        result = __get_flattened_list(
            [__get_nearest_tokens_by_condition(c, condition) for c in root.children]
        )

    # Präsens, Präteritum
    if root.lemma_ in __get_quotation_verbs():
        result = [x for x in root.children if x.dep_ == "oc"]

    if len(result) < 1:
        raise _NotFoundError()

    return result[0]


def __get_subject(node: Token) -> str:
    return __get_text_from_tree(__get_subject_node(node))


def __get_quote(node: Token) -> str:
    return __get_text_from_tree(__get_quote_node(node))


def __get_syntactic_quote(node: Token) -> Optional[Quote]:
    try:
        position_in_text = node.idx
        subject = __get_subject(node)
        citation = __get_quote(node)
        citation_verb = __get_quote_node(node).head.text

        return Quote(
            position_in_text,
            citation,
            subject,
            citation_verb,
        )
    except _NotFoundError:
        return None


def print_nltk_tree(text: str) -> None:
    """Print a nltk parse tree for the given text"""

    def tok_format(tok: Token) -> str:
        return "_".join([tok.orth_, tok.dep_])

    def to_nltk_tree_(node: Token) -> Tree:
        if node.n_lefts + node.n_rights > 0:
            return Tree(
                tok_format(node), [to_nltk_tree_(child) for child in node.children]
            )
        return tok_format(node)

    doc = __get_nlp()(text)
    _ = [to_nltk_tree_(sent.root).pretty_print() for sent in doc.sents]


def get_syntactic_quotes(string: str) -> List[Quote]:
    """Get all syntactic quotes from a given string"""
    roots = __get_roots(string)
    quotes = map(__get_syntactic_quote, roots)
    return list(filter(lambda x: x is not None, quotes))  # type: ignore
