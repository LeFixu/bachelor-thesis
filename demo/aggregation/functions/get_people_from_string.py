"""This Module provides to a given String the people mentioned in it"""

from typing import List
from typing import Tuple
import spacy
from ..classes.person import Person

nlp = spacy.load("de_core_news_lg")
nlp.add_pipe("coreferee")

# Liste von Wörtern die NER fälschlicherweise als Person intepretiert
ner_blacklist_words = ["Sex", "Corona", "St Gallerin"]

common_substitute_nouns = [
    "Prinz",
    "Ehefrau",
    "Tochter",
    "Sohn",
    "Sohnes",
    "König",
    "Expert",
    "Prinzessin",
    "Herzog",
    "Herzogin",
    "Graf",
    "Gräfin",
    "Kaiser",
    "Zar",
    "Kaiserin",
    "Zariza",
    "Chef",
    "Feministin",
]
common_substitute_nouns = [s.lower() for s in common_substitute_nouns]


def __remove_duplicates_in_ner_list(
    ner_people: List[Tuple[List[str], List[int]]]
) -> List[Tuple[List[str], List[int]]]:
    """
    This method removes duplicates from a list of NER people
    """

    unique_list: List[Tuple[List[str], List[int]]] = []
    for sublist in ner_people:
        is_duplicate = False
        for unique_sublist in unique_list:
            if (
                all(name in unique_sublist[0] for name in sublist[0])
                or all(name in sublist[0] for name in unique_sublist[0])
                or all(name[:-1] in sublist[0] for name in unique_sublist[0])
                or all(name[:-1] in unique_sublist[0] for name in sublist[0])
            ):
                is_duplicate = True
                if len(sublist[0]) > len(unique_sublist[0]):
                    sublist[1].extend(unique_sublist[1])
                    unique_list.remove(unique_sublist)
                    unique_list.append(sublist)
                else:
                    unique_sublist[1].extend(sublist[1])
                break
        if not is_duplicate:
            unique_list.append(sublist)

    return unique_list


def __get_unique_ner_people_list(
    nlp_result: spacy.tokens.doc.Doc,
) -> List[Tuple[List[str], List[int]]]:
    """
    This method creates a unique list of NER People
    """
    ner_people_list = []
    for ent in nlp_result.ents:
        if ent.label_ == "PER":
            position_in_text: int = int((ent.start_char + ent.end_char) / 2)
            clean_text = ent.text.replace(",", "").replace(".", "")
            # weil es nur das vor : nehmen soll wie in "Fritz Schenkel: «Ich bleibe optimistisch."
            clean_text = clean_text.split(":")[0]
            if not clean_text.lower() in [x.lower() for x in ner_blacklist_words]:
                ner_people_list.append((clean_text.split(" "), [position_in_text]))

    # clean ner_people_list from dublicates
    return __remove_duplicates_in_ner_list(ner_people_list)


def __get_clean_coref_list(nlp_result: spacy.tokens.doc.Doc) -> List[str]:
    """
    This method creates a clean list of coref clusters
    """
    coref_chain = nlp_result._.coref_chains

    clean_coref_list = []

    for i in coref_chain:
        line = i.pretty_representation
        for char in line:
            if char.isdigit() or char in "(),:[]":
                line = line.replace(char, "")

        clean_coref_list.append(line.lower())

    return clean_coref_list


def __handle_substitute_nouns(person: Person, person_words: List[str]) -> List[str]:
    person_name = []
    for noun in person_words:
        if noun.lower() in common_substitute_nouns:
            person.substitute_nouns.append(noun)
        elif any(
            substitute_noun in noun.lower()
            for substitute_noun in common_substitute_nouns
        ):
            person.substitute_nouns.append(noun)
        else:
            person_name.append(noun)
    return person_name


def __get_people_from_ner_coref(
    ner_people_list: List[Tuple[List[str], List[int]]], coref_list: List[str]
) -> List[Person]:
    """
    This method creates people with the help of the NER list and the coref list
    """
    people = []

    for person_words in ner_people_list:
        new_person = Person("", "", [], [], [], [])
        for person_word in person_words[0]:
            for coref_entry in coref_list:
                if person_word.lower() in coref_entry:
                    pos_res = nlp(coref_entry)
                    for word in pos_res:
                        if word.pos_ == "PRON":
                            new_person.pronouns_and_articles.append(word.text)
                        if word.pos_ == "DET":
                            new_person.pronouns_and_articles.append(word.text)
                        if word.pos_ == "NOUN":
                            new_person.substitute_nouns.append(word.text)

        # handle substitute nouns
        person_name = __handle_substitute_nouns(new_person, person_words[0])

        # wenn keine Namen sondern nur substitute_nouns gefunden,
        #  dann wird neue Person nicht liste hinzugefügt
        if len(person_name) > 0:
            new_person.first_name = person_name[0]
            if len(person_name) > 1:
                # um Nachnamen wie Le Clos oder von Niederhaeusern zu erkennen
                last_name = " ".join(person_name[1:])
                new_person.last_name = last_name

            new_person.positions_in_text = person_words[1]

            people.append(new_person)

    return people


def get_people_from_string(raw_text: str) -> List[Person]:
    """
    This method provides to a given String the people mentioned in it
    """
    result = nlp(raw_text)

    ner_people_list = __get_unique_ner_people_list(result)
    clean_coref_list = __get_clean_coref_list(result)

    return __get_people_from_ner_coref(ner_people_list, clean_coref_list)


def get_person_from_string(string_containing_person: str) -> Person:
    """Get a person object from string"""
    split_parts = string_containing_person.split(" ")

    person = Person("", "", [], [], [], [])
    if len(split_parts) < 2:
        person.last_name = split_parts[0]
    else:
        person.first_name = split_parts[0]
        person.last_name = split_parts[1]

        if len(split_parts) > 2:
            person.substitute_nouns = split_parts[2:]

    return person


if __name__ == "__main__":
    TEST_STR = """
    Sie war von 2017 bis 2020 Frankreichs erste Ministerin für die Gleichheit zwischen Frauen und Männern. Dank ihr sind sexistische Beleidigungen in Frankreich strafbar. Seit ihrer Amtszeit zählt Sex mit Jugendlichen unter 16 Jahren in Frankreich vor Gericht als Vergewaltigung. Und sie ist nun wohl die erste französische Politikerin auf dem Cover des französischen «Playboy».
    Die Rede ist von der Feministin und Staatssekretärin Marlène Schiappa. Derzeit ist sie in dem Land die Staatsministerin für Staatsbürgerschaft. Dass sie das Cover des Magazins ziert, sorgt für Furore. Vor allem bei politischen Gegner:innen und Kolleg:innen stossen ihre Fotos auf Kritik – und das, obwohl Schiappa darauf nicht einmal hüllenlos abgelichtet ist.
    In dem dazugehörigen Titel-Interview sprach die 40-Jährige laut Medienberichten auf zwölf Seiten über die Rechte von Frauen und LGBTQ-Themen. Worüber Frankreich nun spricht, ist aber nicht der Inhalt des Interviews, sondern eben doch der tiefe Ausschnitt, den Schiappas Kleid gehabt haben soll – und der Zeitpunkt der Veröffentlichung.
    «Playboy»-Titel stösst vor allem wegen Rentenreform sauer auf
    So soll Premierministerin Élisabeth Borne laut Medienberichten am Wochenende mit der Staatssekretärin über das Thema gesprochen haben. Oder, wie der Spiegel den Sender BFMTV zitiert, eher geschimpft. Sie bezeichnete das Interview demnach als «nicht angemessen». Vor allem wegen des Zeitpunktes.
    Damit spielte Borne wohl auf die landesweiten Unruhen wegen der umstrittenen Rentenreform an. Eine Grünen-Politikerin vermutete hinter der «Playboy»-Story sogar ein Ablenkungsmanöver. 
    """

    print(get_people_from_string(TEST_STR))
