"""This Module provides to a given Person the Gender to it"""

from typing import Tuple
from typing import List
from typing import Optional
import logging as log
import pandas as pd  # type:ignore
from genderize import Genderize, GenderizeException  # type:ignore
from gender_gap_tracker.classes.person import Person
from gender_gap_tracker.classes.genderized_person import GenderizedPerson
from gender_gap_tracker.classes.genderized_person import Gender

# Load Data from Excel
female_names_df = pd.read_excel(
    "./gender_gap_tracker/functions/data/female.xlsx",
    engine="openpyxl",
    index_col=None,
    header=0,
)
female_names_df["firstname"] = female_names_df["firstname"].str.lower()
male_names_df = pd.read_excel(
    "./gender_gap_tracker/functions/data/male.xlsx",
    engine="openpyxl",
    index_col=None,
    header=0,
)
male_names_df["firstname"] = male_names_df["firstname"].str.lower()

pronouns_and_articles_female = ["sie", " diejenige", "dieselbe", "ihres"]
pronouns_and_articles_male = [
    "er",
    "der",
    "sein",
    "seine",
    "seinem",
    "seiner",
    "ihm",
    "derjenige",
    "derselbe",
]
common_substitute_nouns_male = [
    "prinz",
    "eheman",
    "sohn",
    "sohnes",
    "könig",
    "experte",
    "herzog",
    "graf",
    "kaiser",
    "chef",
]
common_substitute_nouns_female = [
    "ehefrau",
    "tochter",
    "königin",
    "expertin",
    "prinzessin",
    "herzogin",
    "gräfin",
    "kaiserin",
    "zariza",
    "chefin",
    "feministin",
]


HAS_REACHED_API_LIMIT = False


def __get_gender_from_api(firstname: str) -> Tuple[Optional[Gender], float]:
    """
    This method gets the gender from the genderize.io API
    """
    global HAS_REACHED_API_LIMIT # pylint: disable=global-statement
    gender_api: Optional[Gender] = None
    prob_api: float = 0.0

    try:
        res_list = Genderize().get([firstname])
    except GenderizeException as exception:
        if exception.args[1] == 429:
            log.warning("Received HTTP code 429 on Genderize API!")
            HAS_REACHED_API_LIMIT = True
            return (None, 0.0)
    except Exception as exeption:
        log.exception("Fail to process genderize API request: %s", exeption)
        return (None, 0.0)

    gender_api_str = res_list[0]["gender"]
    prob_api = float(res_list[0]["probability"])

    if gender_api_str == "male":
        gender_api = Gender.MALE
    elif gender_api_str == "female":
        gender_api = Gender.FEMALE

    return (gender_api, prob_api)


def __check_pronouns_substitute_nouns(
    pronouns: List[str], substitute_nouns: List[str]
) -> Tuple[Optional[Gender], float]:
    """
    This method gets the gender from comparing given pronouns
    to our defined prounouns list per gender
    """
    female_pron_sub_noun_counter = 0
    male_pron_sub_noun_counter = 0
    gender_pronouns: Optional[Gender] = None

    for pron in pronouns:
        if pron.lower() in pronouns_and_articles_female:
            female_pron_sub_noun_counter = female_pron_sub_noun_counter + 1
            gender_pronouns = Gender.FEMALE
        elif pron.lower() in pronouns_and_articles_male:
            male_pron_sub_noun_counter = male_pron_sub_noun_counter + 1
            gender_pronouns = Gender.MALE

    for sub_noun in substitute_nouns:
        if sub_noun.lower() in common_substitute_nouns_female:
            female_pron_sub_noun_counter = female_pron_sub_noun_counter + 1
            gender_pronouns = Gender.FEMALE
        elif sub_noun.lower() in common_substitute_nouns_male:
            male_pron_sub_noun_counter = male_pron_sub_noun_counter + 1
            gender_pronouns = Gender.MALE

    if (female_pron_sub_noun_counter == 0 and male_pron_sub_noun_counter > 0) or (
        male_pron_sub_noun_counter == 0 and female_pron_sub_noun_counter > 0
    ):
        return (gender_pronouns, 1.0)

    sum_pron = female_pron_sub_noun_counter + male_pron_sub_noun_counter
    if female_pron_sub_noun_counter > male_pron_sub_noun_counter:
        prob_pron = female_pron_sub_noun_counter / sum_pron
        gender_pronouns = Gender.FEMALE
    elif female_pron_sub_noun_counter < male_pron_sub_noun_counter:
        prob_pron = male_pron_sub_noun_counter / sum_pron
        gender_pronouns = Gender.MALE
    elif female_pron_sub_noun_counter == 0 and male_pron_sub_noun_counter == 0:
        prob_pron = 0
        gender_pronouns = None
    else:
        prob_pron = 0.5
        gender_pronouns = None

    return (gender_pronouns, prob_pron)


def __check_list_from_bfs(firstname: str) -> Tuple[Optional[Gender], float]:
    """
    This method gets the gender from checking the bfs names list per gender
    """
    gender_bfs_counter = 0
    female_bfs_counter = 0
    male_bfs_counter = 0
    gender_bfs: Optional[Gender] = None

    loc_female = female_names_df.loc[(female_names_df["firstname"] == firstname)]
    loc_male = male_names_df.loc[(male_names_df["firstname"] == firstname)]
    if loc_female.any().all():
        gender_bfs = Gender.FEMALE
        female_bfs_counter = loc_female["Total"].values[0]
        gender_bfs_counter = gender_bfs_counter + 1
    if loc_male.any().all():
        gender_bfs = Gender.MALE
        male_bfs_counter = loc_male["Total"].values[0]
        gender_bfs_counter = gender_bfs_counter + 1

    if gender_bfs_counter > 1:
        sum_bfs = female_bfs_counter + male_bfs_counter
        if female_bfs_counter > male_bfs_counter:
            prob_list_bfs = female_bfs_counter / sum_bfs
            gender_bfs = Gender.FEMALE
        elif female_bfs_counter < male_bfs_counter:
            prob_list_bfs = male_bfs_counter / sum_bfs
            gender_bfs = Gender.MALE
        elif female_bfs_counter == 0 and male_bfs_counter == 0:
            prob_list_bfs = 0
            gender_bfs = None
        else:
            prob_list_bfs = 0.5
            gender_bfs = None

        return (gender_bfs, prob_list_bfs)
    if gender_bfs_counter == 1:
        return (gender_bfs, 1.0)

    # kein match in listen
    return (None, 0.0)


def get_genderized_person(person: Person) -> GenderizedPerson:
    """
    This method gets the gender to a given Person
    """

    if len(person.first_name) < 1 and len(person.last_name) < 1:
        return GenderizedPerson(
            person.first_name,
            person.last_name,
            person.salutation,
            person.pronouns_and_articles,
            person.substitute_nouns,
            person.positions_in_text,
            gender=None,
            probability=0.0,
        )

    clean_firstname = person.first_name.lower()

    res_list_bfs = __check_list_from_bfs(clean_firstname)
    gender_bfs: Optional[Gender] = res_list_bfs[0]
    prob_bfs: float = res_list_bfs[1]

    res_list_pronouns = __check_pronouns_substitute_nouns(
        person.pronouns_and_articles, person.substitute_nouns
    )
    gender_pron: Optional[Gender] = res_list_pronouns[0]
    prob_pron: float = res_list_pronouns[1]

    # compare bfs and pron results
    gender_bfs_pron: Optional[Gender] = None
    prob_bfs_pron = 0.0
    if prob_bfs == 0.0:
        prob_bfs_pron = prob_pron
        gender_bfs_pron = gender_pron
    elif prob_pron == 0.0:
        prob_bfs_pron = prob_bfs
        gender_bfs_pron = gender_bfs
    elif gender_bfs == gender_pron:
        prob_bfs_pron = (prob_bfs + prob_pron) / 2
        gender_bfs_pron = gender_bfs

    if prob_bfs_pron > 0.66 or HAS_REACHED_API_LIMIT:
        return GenderizedPerson(
            person.first_name,
            person.last_name,
            person.salutation,
            person.pronouns_and_articles,
            person.substitute_nouns,
            person.positions_in_text,
            gender=gender_bfs_pron,
            probability=prob_bfs_pron,
        )

    log.debug(
        "pob_bfs_pron is lower than 0.66 (is %f) --> check gender API", prob_bfs_pron
    )
    res_list_api = __get_gender_from_api(clean_firstname)
    gender_genderize_api: Optional[Gender] = res_list_api[0]
    prob_genderize_api: float = res_list_api[1]
    gender_bfs_pron_api: Optional[Gender] = None

    # compare bfs_pron and api results
    prob_bfs_pron_api = 0.0
    if prob_bfs_pron == 0.0:
        prob_bfs_pron_api = prob_genderize_api
        gender_bfs_pron_api = gender_genderize_api
    elif prob_genderize_api == 0.0:
        prob_bfs_pron_api = prob_bfs_pron
        gender_bfs_pron_api = gender_bfs_pron
    elif gender_bfs_pron == gender_genderize_api:
        prob_bfs_pron_api = (prob_bfs_pron + prob_genderize_api) / 2
        gender_bfs_pron_api = gender_bfs_pron
    elif gender_bfs_pron != gender_genderize_api:
        if prob_bfs_pron < prob_genderize_api:
            prob_bfs_pron_api = prob_genderize_api
            gender_bfs_pron_api = gender_genderize_api
        else:
            prob_bfs_pron_api = prob_bfs_pron
            gender_bfs_pron_api = gender_bfs_pron

    if gender_bfs_pron_api is not None:
        return GenderizedPerson(
            person.first_name,
            person.last_name,
            person.salutation,
            person.pronouns_and_articles,
            person.substitute_nouns,
            person.positions_in_text,
            gender=gender_bfs_pron_api,
            probability=prob_bfs_pron_api,
        )

    # return GenderizedPerson without gender and prob
    return GenderizedPerson(
        person.first_name,
        person.last_name,
        person.salutation,
        person.pronouns_and_articles,
        person.substitute_nouns,
        person.positions_in_text,
        gender=None,
        probability=0.0,
    )


if __name__ == "__main__":

    test_person = Person("Albert", "", [], [], [], [310, 1069])

    genderized_person = get_genderized_person(test_person)

    print("")
    print(genderized_person)
