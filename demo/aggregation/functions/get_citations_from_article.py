"""Execute citation extraction"""

from typing import  List
from datetime import datetime
from ..classes.citation_with_person import CitationWithPerson
from ..functions.assign_people_to_citations import assign_people_to_citations
from ..functions.get_citations_from_string import get_syntactic_quotes
from ..functions.get_people_from_string import get_people_from_string
from ..functions.get_genderized_person import get_genderized_person



def get_citations_from_article(text: str) -> List[CitationWithPerson]:

    start = datetime.now()
    article_text = text
    people = get_people_from_string(article_text)
    genderized_people = map(get_genderized_person, people)
    citations = get_syntactic_quotes(article_text)
    print(citations)
    citations_with_person = assign_people_to_citations(
        genderized_people, citations
    )

    time_diff = datetime.now() - start

    return citations_with_person
