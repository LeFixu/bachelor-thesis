# Bachelor Thesis 2023 - Gender Gap Tracker Schweizer Medien

## Ordnerstruktur
| Ordner                       | Bedeutung                                                                                                                              |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| data                         | Backup der MongoDB mit 2 Collections: analyzed_articles => Artikel mit Zitaten, unique_articles => Bereinigte Artikel (ohne Duplikate) |
| documentation                | LaTex Dokumentation sowie Feedbacks etc.                                                                                               |
| gender_gap_tracker           | Produktiver Code => alle Python Files in diesem Verzeichnis entsprechen dem PEP8 Standard und sind mit MyPy Typisiert                                                                                                                       |
| gender_gap_tracker/functions | Funktionen zum Extrahieren der Zitate / Personen etc                                                                                   |
| gender_gap_tracker/grading   | Bewertungsalgorithmen und Testsets                                                                                                     |
| gender_gap_tracker/utils     | DB Konnektoren und andere Infrastrukturfunktionen                                                                                      |
| poc                          | Proof Of Concept => Ordner mit Skripts und Notebooks für die Auswertung, Datenbereinigung oder Experimente (Nicht gelinteter Code)     |
| poc/document_similarity      | Datenbereinigung                                                                                                                       |
| project_management           | Zeitplan, Konversationen und Meetingprotokolle                                                                                         |
| results                      | Aggregierte Resultate und Abfragequery                                                                                                 |

## Auswertung ausführen

Verwende conda mit Python Version 3.10

Installiere dependencies
```
conda env create -f environment.yml
```

MongoDB in lokalem Docker Container starten
```
docker run -d -p 27017:27017 --name mongoDB mongo:latest
```

In der MongoDB eine Collection `unique_articles` mit Daten aus `data/unique_articles...` erstellen

Auswertung starten
```
python -m gender_gap_tracker
```
## Datenbereinigung ausführen

Verwende conda mit Python Version 3.10

Installiere dependencies
```
conda env create -f environment.yml
```

MongoDB in lokalem Docker Container starten
```
docker run -d -p 27017:27017 --name mongoDB mongo:latest
```

In der MongoDB eine Collection `articles` mit Daten aus `data/unique_articles...` erstellen.

Einige Duplikate einfügen (sonst wird das Resultat dasselbe sein)

Auswertung starten
```
cd poc/document_similarity
python write_unique_articles_to_file.py
```