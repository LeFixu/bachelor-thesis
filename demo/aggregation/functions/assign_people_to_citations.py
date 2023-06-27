# pylint: disable=redefined-outer-name
"""
This module provides functionality to match people and citation subjects
"""

from statistics import mean
from typing import Iterable, Optional, Tuple, List
from ..classes.genderized_person import GenderizedPerson
from ..classes.citation import Quote
from ..classes.citation_with_person import CitationWithPerson
from ..utils.string_similarity import get_string_similarity

__REQUIRED_MATCHING_PROBABILITY = 0.1
__PARTIAL_NAME_MATCH_PROBABILITY_VALUE = 0.75
__FULL_NAME_MATCH_PROBABILITY_VALUE = 1
__PRONOUN_MATCH_PROBABILITY_VALUE = 0.5


def __get_min_distance_to_person(citation: Quote, person: GenderizedPerson) -> int:
    mean_position_of_citation = int(mean(citation.position_in_text))
    return min(
        map(
            lambda position: position - mean_position_of_citation,
            person.positions_in_text,
        ),
        key=abs,
    )


# TODO: use lewis edit distance string similarity instead of sequence matcher
def __get_matching_probability(subject: str, person: GenderizedPerson) -> float:
    subject_lower = subject.lower()
    max_substitute_noun_match = max(
        [0]  # ensure that max doesn't fail on empty list, so append a 0
        + list(
            map(
                lambda sn: get_string_similarity(sn.lower(), subject_lower),
                person.substitute_nouns,
            )
        )
    )

    fn_e = len(person.first_name) < 1  # is first name empty?
    ln_e = len(person.last_name) < 1  # is last name empty?

    # Both first_name and last_name are empty
    if fn_e and ln_e:
        return max_substitute_noun_match

    fn_lower = person.first_name.lower()
    ln_lower = person.last_name.lower()

    # first_name is set but last_name is not
    if not fn_e and ln_e:
        if fn_lower in subject_lower:
            fn_match_value = __PARTIAL_NAME_MATCH_PROBABILITY_VALUE
        else:
            fn_match_value = 0
        return max(fn_match_value, max_substitute_noun_match)

    # last_name is set but first_name is not
    if fn_e and not ln_e:
        if ln_lower in subject_lower:
            ln_match_value = __PARTIAL_NAME_MATCH_PROBABILITY_VALUE
        else:
            ln_match_value = 0
        return max(ln_match_value, max_substitute_noun_match)

    # check for full match
    if fn_lower in subject_lower and ln_lower in subject_lower:
        return __FULL_NAME_MATCH_PROBABILITY_VALUE

    pronoun_similarities = [
        __PRONOUN_MATCH_PROBABILITY_VALUE
        for x in person.pronouns_and_articles
        if x == subject_lower
    ]

    return max(
        pronoun_similarities
        + [
            max_substitute_noun_match,
            get_string_similarity(subject_lower, fn_lower),
            get_string_similarity(subject_lower, ln_lower),
            get_string_similarity(subject_lower, " ".join([fn_lower, ln_lower])),
            get_string_similarity(subject_lower, " ".join([ln_lower, fn_lower])),
        ]
    )


def __get_person_for_citation(
    citation: Quote, people: Iterable[GenderizedPerson]
) -> Optional[Tuple[GenderizedPerson, float]]:
    people_sorted_by_distance = sorted(
        people, key=lambda p: __get_min_distance_to_person(citation, p)
    )
    for person in people_sorted_by_distance:
        matching_probability = __get_matching_probability(citation.subject, person)
        if matching_probability >= __REQUIRED_MATCHING_PROBABILITY:
            return (person, matching_probability)
    return None


def assign_people_to_citations(
    people: Iterable[GenderizedPerson], citations: Iterable[Quote]
) -> List[CitationWithPerson]:
    """
    Tries to assign a person to each citation. Filters out citations,
    where no matching person could be found
    """
    citations_with_person_nullable = map(
        lambda c: (c, __get_person_for_citation(c, people)), citations
    )
    citations_with_person = filter(
        lambda x: x[1] is not None, citations_with_person_nullable
    )

    return list(
        map(
            lambda cwp: CitationWithPerson(cwp[0], cwp[1][0], cwp[1][1]),  # type: ignore
            citations_with_person,
        )
    )


if __name__ == "__main__":
    from .get_citations_from_string import get_syntactic_quotes
    from .get_genderized_person import get_genderized_person
    from .get_people_from_string import get_people_from_string

    ARTICLE = """
Seine Amtszeit endete mit einem Drama. Nur Stunden bevor er das Gemeindepräsidium von Sumiswald abgeben wollte, musste Fritz Kohler (EDU) zu seinem letzten Ernstfall ausrücken. Ein ehemaliges Bauernhaus in Wasen stehe in Flammen, hörte er am Telefon, als er letzten Silvester morgens um halb fünf Uhr aus dem Schlaf gerissen wurde.

In eindrücklichen Worten schilderte Kohler einen Monat später, was er in den folgenden Stunden erlebt hat. Er erzählte von der älteren Bewohnerin, die noch am gleichen Tag ihren Verbrennungen erlag, und von ihrem Sohn, der schwer verletzt ins Spital gebracht wurde. Von den weiteren Familienangehörigen auch, für die die Gemeinde in kürzester Zeit eine Bleibe finden musste. Zwei von ihnen begleitete Kohler an Neujahr zuerst auf den Brandplatz, später nahm er sie zu sich nach Hause. Dort hätten die beiden «langsam zu erzählen begonnen» und so einen ersten Schritt in der Verarbeitung gemacht.

Zwei Tage später übernahm Parteikollege und Nachfolger Martin Friedli – und hatte als erste Amtshandlung gleich den Grossbrand am Hals. Er verspüre grossen Respekt vor dem, was nun auf ihn zukomme, sagte Friedli damals. Ob er in solch schwierigen Situationen einen ähnlich guten Draht zu den Leuten finden werde wie sein Vorgänger?
Die Rolle im Krisenfall

Gemeindepräsidentinnen und Gemeindepräsidenten haben nicht nur die Aufgabe, sich um die Finanzen, die Schulen oder das Bauwesen in ihrem Dorf zu kümmern. Ihr Wissen und ihre Mithilfe sind auch gefragt, sobald ein Brand, eine Naturkatastrophe oder auch ein Verbrechen die Menschen in ihrem Umfeld erschüttert – und dann finden sie sich unmittelbar im Strudel der Ereignisse wieder.
Neben der Polizei war auch der Gemeindepräsident vor Ort: Szene vom Grossbrand, der in Wasen ein ehemaliges Bauernhaus verwüstete.
Neben der Polizei war auch der Gemeindepräsident vor Ort: Szene vom Grossbrand, der in Wasen ein ehemaliges Bauernhaus verwüstete.
Foto: Marcel Bieri

Die operativen und fachlichen Arbeiten können sie zwar getrost den Fachleuten von Feuerwehr und Polizei überlassen. «Diese sind entsprechend ausgebildet und verfügen auch über Spezialkenntnisse», schreibt Daniel Bichsel (SVP), der in Zollikofen selber Gemeindepräsident ist und den Verband bernischer Gemeinden präsidiert. Aber: Noch immer nehme das Amt eine besondere Stellung ein. Der Präsident, die Präsidentin sei quasi das Gesicht der Gemeinde und als solches auch dafür gewählt, «die Gemeinde und ihre Gemeinschaft zu repräsentieren». In dieser «gesellschaftlichen und sozialen Funktion» gehe es darum, Anteilnahme, Verbundenheit mit den Betroffenen sowie solidarische Unterstützung zu signalisieren.

Und wieder stellt sich die bange Frage: Ob man das einfach so kann, auf diese Aufgabe vorbereitet ist?
Schüsse in Niederbipp

Nein. Die Antwort von Sibylle Schönmann (SVP) ist klar. In ihrer bisher siebenjährigen Amtszeit hat die Gemeindepräsidentin von Niederbipp etliche ausserordentliche Ereignisse bewältigt, mehrfach hat es in dieser Zeit im Dorf gebrannt. Letztmals zünftig gefordert war sie an einem Sonntag im vergangenen Juli, als nach einer tödlichen Schiesserei um vier Uhr früh das Telefon klingelte. «Man wird jedes Mal ins kalte Wasser geworfen», sagt sie.

    «Ich habe gelernt, mit schwierigen Situationen umzugehen.»
    Sibylle Schönmann, Gemeindepräsidentin von Niederbipp

Sie sei dann immer froh, fährt die 54-Jährige fort, «dass ich nicht mehr zwanzig bin». In ihrem Leben habe sie schon etliche schwierige Situationen meistern müssen. «Ich habe gelernt, damit umzugehen.»

Trotzdem ist die Verunsicherung jedes Mal gross. Das war an jenem Sonntagmorgen nicht anders. «Ich wusste nicht, was mich erwartet, und auch nicht, ob noch geschossen wird», erinnert sie sich an die bangen Minuten auf dem Weg zum Tatort. Umso froher war sie, dass gleich ein Rapport stattfand und sie die wichtigsten Infos mitbekam. «Der Mensch will sich immer an etwas möglichst Greifbarem halten können.» Ihr jedenfalls habe enorm geholfen, nicht mehr derart in der Luft zu hängen wie zu Beginn.
Froh, zu tun zu haben

Schönmann zeigt deshalb Verständnis dafür, dass die Öffentlichkeit nach einem derart schweren Vorfall möglichst rasch möglichst viel erfahren will. «Die Medienarbeit ist mir wichtig», sagt sie – um gleich zu relativieren: Klar dürfe auch sie nicht mehr preisgeben, als mit den Ermittlern der Polizei abgesprochen sei. Umgekehrt biete ein Auftritt zum Beispiel vor der Kamera des lokalen Fernsehens auch eine Chance, Gerüchte zurechtzurücken. Denn ja, Falschinformationen seien jeweils sehr schnell im Umlauf.
War im vergangenen Juli gefordert: Die Niederbipper Gemeindepräsidentin Sibylle Schönmann wurde zum Ort des Tötungsdelikts gerufen.
War im vergangenen Juli gefordert: Die Niederbipper Gemeindepräsidentin Sibylle Schönmann wurde zum Ort des Tötungsdelikts gerufen.
Foto: Raphael Moser

Zuerst allerdings hatte sie an diesem frühen Morgen andere Aufgaben zu bewältigen. Keine fachlichen, wie sie ebenfalls betont. Dafür seien schliesslich Polizei, Feuerwehr und Sanität auf dem Platz. «Mich beeindruckt immer wieder von neuem, wie gut organisiert die Blaulichtorganisationen sind.»

Schönmann organisierte stattdessen Büroräume, in denen die Polizei ihre Abklärungen vor Ort treffen konnte, sorgte weiter für eine erste Verpflegung. Dabei wurde ihr bewusst, dass es gar nicht so einfach ist, am Wochenende so früh zu Sandwiches zu kommen. «Ich war in diesem Moment aber einfach froh, beschäftigt zu sein und meinen Beitrag leisten zu können.»
Fragen, die auftauchen

Denn ja, solche Einsätze hinterlassen auch nach sieben Jahren Spuren. «Zuerst funktioniert man einfach», fährt Schönmann fort. Nach ein paar Stunden oder vielleicht auch Tagen tauchten dann aber bohrende Fragen auf. Im Fall des Tötungsdelikts etwa die: Hätte die Gemeinde, hätte sie als deren Präsidentin vor dem verhängnisvollen Wochenende etwas merken sollen? 

«Am liebsten würde man in einer solchen Situation das Geschehene rückgängig machen», fährt sie fort. Bei einem Tötungsdelikt gehe das naturgemäss nicht. Umso stärker sei das Bedürfnis, sicherzustellen, dass sich so etwas nicht wiederhole. Schönmann kommt zurück auf ihre Medienauftritte nach dem Vorfall: «Mir war wichtig, die Leute dazu aufzurufen, wachsam zu sein und die Behörden auf problematische Situationen hinzuweisen.»

    «Es gibt Taten, die aus dem Nichts kommen. Das muss man so akzeptieren können.»
    Sibylle Schönmann, Gemeindepräsidentin von Niederbipp

Dass sie im konkreten Fall von Fachleuten hörte, nicht jedes Delikt lasse sich voraussehen, wirkte beruhigend. «Es gibt Taten, die aus dem Nichts kommen. Das muss man so akzeptieren können.»
Stromschlag in Kehrsatz

Mehrere Brände sowie Anfang Jahr, als ein Mann mutmasslich seine Frau erdrosselte, ebenfalls ein Tötungsdelikt – in Kehrsatz stand Gemeindepräsidentin Katharina Annen (FDP) in den letzten zehn Jahren vor ähnlichen Herausforderungen. Am meisten zu schaffen machte ihr ein tragischer Unfall vor sechs Jahren: Ein 6- und ein 7-jähriger Bub nahmen einen eingesteckten Föhn mit in die volle Badewanne und erlitten einen tödlichen Stomschlag.
Vom tödlichen Unfall in der Badewanne erschüttert: Gemeindepräsidentin Katharina Annen hatte die beiden Buben persönlich gekannt.
Vom tödlichen Unfall in der Badewanne erschüttert: Gemeindepräsidentin Katharina Annen hatte die beiden Buben persönlich gekannt.
Foto: Nicole Philipp

Sie habe die beiden von der Tagesschule her gekannt, erzählt Annen, die dort regelmässig mitarbeitet. «Die beiden lebten hier, hatten hier auch ihre Gspäändli. Wenn man die Betroffenen so eng kennt, ist man automatisch erschüttert.» Eine Woche später kontaktierte sie deshalb die betroffene Mutter und fragte, wie es ihr gehe. «Nicht als Gemeindepräsidentin, sondern als Privatperson», wie sie betont.

Direkt involviert ist Annen bei solch tragischen Ereignissen in der Regel nicht. «Für die operativen Arbeiten wie die Suche nach Unterkünften für Brandgeschädigte ist bei uns die Verwaltung zuständig.» Sie komme offiziell erst ins Spiel, wenn eine Reaktion der Gemeinde gefragt sei. «Dann überlege ich mir jeweils sehr genau, was ich sage.» Und wo – nach dem Unfall mit dem Föhn etwa schlug das Team des lokalen Fernsehsenders das betroffene Quartier vor, sie aber trat nur im Gemeindehaus vor die Kamera.
Wie die Polizei handelt

Erst letztes Wochenende galt es in Boll in der Gemeinde Vechigen für Gemeindepräsidentin Sibylle Schwegler (SVP) ernst. In einem Restaurant fielen Schüsse, ein Mann starb – sie selber habe direkt nichts mitbekommen, sagt Schwegler, sei aber von der Polizei noch vor der Öffentlichkeit informiert worden. Im Dorf selber nimmt sie kaum Diskussionen über den Vorfall wahr. Weil die Identität des Toten offiziell noch nicht bekannt sei, das Opfer also noch kein Gesicht habe, mutmasst sie.

Mal ist die Gemeindepräsidentin vor Ort, mal wird sie lediglich mit etwas Vorsprung informiert – wie das kommt? Die Frage geht an die Kantonspolizei, und die gibt zur Antwort: Kein Ereignis sei wie das andere, wer genau wann und wie beigezogen werde, hänge von den jeweiligen Umständen ab. Der Entscheid liege bei den Verantwortlichen vor Ort.

Ueli Gfeller (SVP) weiss, was es heisst, als Gemeindepräsident eine Katastrophe bewältigen zu müssen. Als Schangnau im Sommer 2014 vom Rekordhochwasser der Emme geflutet wurde, war er gefordert. Im Frühjahr 2018 wurde sein Einsatz mit der Wahl in den Grossen Rat belohnt. Seine Bekanntheit als Krisenmanager habe ihm wohl geholfen, sagt Gfeller heute. Wobei andere Faktoren wie vorgängige Rücktritte verdienter SVP-Grossräte ebenfalls mitgespielt hätten. 

Mit der Wahl in den Nationalrat schaffte im Herbst 2019 die Bündnerin Anna Giacometti (FDP) einen noch grösseren Sprung. Sie war Gemeindepräsidentin im Bergell, als im Herbst 2017 ein Bergsturz auf das Dorf Bondo niederging. (skk)

In Sumiswald blickt Gemeindepräsident Friedli mittlerweile auf schon fast vier Monate im neuen Amt zurück, und er empfindet noch immer den gleichen Respekt vor seiner Aufgabe wie Anfang Jahr. Im Moment ruht der Kontakt zur betroffenen Familie zwar, schliesslich, sagt er, wolle man sich auch nicht aufdrängen. Bei Fragen zum Wiederaufbau biete die Gemeinde aber weiterhin ihre Hilfe an. «Das Ganze ist sehr tragisch. Ich hoffe, dass wir kein derartiges Feuer mehr erleben müssen.»
    """

    citations = get_syntactic_quotes(ARTICLE)
    people = get_people_from_string(ARTICLE)
    genderized_people = list(map(get_genderized_person, people))

    print(list(map(lambda c: c.subject, citations)))
    print(genderized_people)
    citations_with_person = assign_people_to_citations(genderized_people, citations)

    print()
    print("citations_with_person:")
    for cwp in citations_with_person:
        print(
            f"{cwp.citation.citation} - {cwp.citation.subject} - {cwp.citation.citation_verb}"
        )
        print(f"{cwp.person} - {cwp.matching_probability}")
        print()
# pylint: enable=redefined-outer-name
