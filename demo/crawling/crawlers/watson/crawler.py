"""Watson Crawler"""

import time
import re
import datetime
import traceback
from os import environ
import fnmatch
from bs4 import BeautifulSoup
import requests
from ...utils.db_driver.db_driver import insert_article
from ...utils.db_driver.article import ArticleBuilder, Article
from ...utils.db_driver.db_driver import get_urls
from ...utils.db_driver.url import UrlBuilder, Url
from ...utils.db_driver.source import Source

START_URL = "https://www.watson.ch/"


# A dictionary of filters on attribute values.
# TODO: find links that are not full links like /Bern/
attrs = {"href": re.compile(r"^https:\/\/www\.watson\.ch\/.*$")}

link_blacklist = [
    "*www.watson.ch/videos/*",
    "*www.watson.ch/fr/*",
    "*www.watson.ch/quiz/*",
    "*www.watson.ch/u/meteo*",
    "*www.watson.ch/app*",
]

found_urls_list = []
db_watson_urls = []
new_db_watson_urls = []


def search_links(url: str) -> None:
    """Searches for links on website from given url"""
    try:
        html_text = requests.get(url, timeout=10).text
    except requests.exceptions.ConnectionError as ex:
        traceback.print_exc()
        print(f"Fail to process your command: {ex}")
        return
    except Exception as exeption:
        traceback.print_exc()
        print(f"Fail to process your command: {exeption}")
        return

    soup = BeautifulSoup(html_text, "html.parser")
    links = soup.find_all("a", attrs=attrs)

    for link in links:
        valid_link = True
        for filtering in link_blacklist:
            if fnmatch.fnmatch(link.get("href"), filtering):
                valid_link = False
                break

        if (
            valid_link
            and (link.get("href") not in found_urls_list)
            and (link.get("href") not in db_watson_urls)
        ):
            found_urls_list.append(link.get("href"))


def analyze_web_page(url: str) -> Article:
    """Analyzes if this is a article and then extract data or searches links"""
    try:
        html_text = requests.get(url, timeout=10).text
    except Exception as exeption:
        traceback.print_exc()
        print(f"Fail to process your command: {exeption}")
        return

    soup = BeautifulSoup(html_text, "html.parser")

    story_list = soup.find_all(class_="watson-story__content")
    if len(story_list) != 0:  # --> Artikel mit Text
        story = story_list[0]
        text_elements = story.find_all(
            class_=[
                "watson-snippet__text",
                "watson-snippet__quote-long__text",
                "watson-snippet__quote__text",
            ]
        )
        if len(text_elements) != 0:

            full_text = ""
            for element in text_elements:
                full_text += element.text + "\n"

            # paragraphs
            paragraps = []
            for element in text_elements[:-1]:  # letzer paragraph ignorieren
                if len(element.text) > 0:
                    paragraps.append(element.text)
            if not paragraps:  # list ist empty
                paragraps.append("")

            # title vom Artikel
            title = ""
            title_list = soup.find_all(class_="watson-snippet__title")
            if len(title_list) > 0:
                title = title_list[0].text
                # print(f'title:  {title}')

            # lead vom Artikel
            lead_list = soup.find_all(class_="watson-snippet__lead")
            lead = ""
            if len(lead_list) > 0:
                lead = lead_list[0].text
                # print(f'lead: {lead}')

            # Author
            # 2 arten von author nennungen:
            # https://www.watson.ch/schweiz/svp/770428580-was-lgbtq-menschen-an-der-svp-finden
            # https://www.watson.ch/schweiz/interview/322657143-critical-mass-das-grosse-streitgespraech-zwischen-fdp-und-sp
            author = ""
            container_list = soup.find_all(class_="watson-snippet__authorbox")
            if len(container_list) > 0:
                author_cont_list = container_list[0].find_all(class_="leading-snug")
                if len(author_cont_list) > 0:
                    author_cont = author_cont_list[0]
                    if len(author_cont.text) > 0:
                        author = author_cont.text

            # Veroefentlichung Artikel in Form 04.11.2022, 13:10
            published_list = soup.find_all(
                class_="watson-snippet__shareBubbles__published"
            )
            published = 0
            if len(published_list) > 0:
                published = round(
                    time.mktime(
                        datetime.datetime.strptime(
                            published_list[0].next_sibling.text, "%d.%m.%Y, %H:%M"
                        ).timetuple()
                    )
                )
                # print(published)

            # Updated Artikel
            updated_list = soup.find_all(class_="watson-snippet__shareBubbles__updated")
            updated = 0
            if len(updated_list) > 0:
                updated = round(
                    time.mktime(
                        datetime.datetime.strptime(
                            updated_list[0].next_sibling.text, "%d.%m.%Y, %H:%M"
                        ).timetuple()
                    )
                )
                # print(f'updated: {updated}')

            # insert into DB
            article = (
                ArticleBuilder()
                .with_title(title)
                .with_lead(lead)
                .with_url(url)
                .with_author(author)
                .with_source(Source.WATSON.value)
                .with_published(published)
                .with_updated(updated)
                .with_paragraphs(paragraps)
                .build()
            )

            return article
        else:
            # links suchen und zu Liste hinzu fuegen
            search_links(url)
            print(f"No Articel: {url}")
    else:
        # links suchen und zu Liste hinzu fuegen
        search_links(url)
        print(f"No Articel: {url}")


def _get_watson_link(link: str) -> Url:
    return UrlBuilder().with_url(link).with_source(Source.WATSON.value).build()


if __name__ == "__main__":
    try:
        MAX_LINKS = int(environ["GGT_MAX_WATSON_LINKS_PROCESSED"])
        SLEEP_S = float(environ["GGT_SLEEP"])
    except KeyError:
        MAX_LINKS = 100
        SLEEP_S = 2

    watson_url_objects = get_urls(Source.WATSON)
    db_watson_urls = [o.get("url") for o in watson_url_objects]

    print(f"DB Watson Links Len: {len(db_watson_urls)}")

    search_links(START_URL)
    # print(f'number of first link search is {len(found_urls_list)}')

    # fuer Pipeline
    with open("links.txt", "w", encoding="utf-8") as f:
        for f_link in found_urls_list:
            f.write(f_link + "\n")

    # go thrue link list in for loop
    COUNTER = 0
    start_time = time.time()
    for found_link in found_urls_list:
        # if len(found_link)> 50: # TODO rausnehmen fuer prod
        COUNTER = COUNTER + 1
        if (
            COUNTER <= MAX_LINKS
        ):  # first do max_links links so we dont get blocked from watson
            analyze_web_page(found_link)

            end_time = time.time()
            time_dif = end_time - start_time
            if time_dif < SLEEP_S:
                time.sleep(SLEEP_S - time_dif)

            # print status queue and new articles found
            if COUNTER % 100 == 0:
                print("")
                print("---------- STATUS ---------- : ")
                print(f"links in queue at the time: {len(found_urls_list)}")
                print(f"found new article links at the time: {len(new_db_watson_urls)}")
                print("")

            start_time = time.time()

    # print stuff
    print("")
    print("---------- END STATUS ---------- : ")
    print(f"found links in queue: {len(found_urls_list)}")

    print(
        f"not processed links in queue: {len(found_urls_list) - len(new_db_watson_urls)}"
    )

    print(f"found new article links: {len(new_db_watson_urls)}")
