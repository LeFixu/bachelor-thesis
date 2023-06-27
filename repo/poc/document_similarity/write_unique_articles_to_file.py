import json
import ijson
import sys
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd



def export_clean_articles(file_name: str, source: str) -> None:
    # load Data from JSON
    with open(file_name, 'rb') as file:
        data_json = ijson.items(file, 'item')
            
        # Filtern nach Attribut "source" mit Wert "blick"
        data_blick = [d for d in data_json if d['source'] == source]

    print(f'len start data {source} {len(data_blick)}')


    # Dokumente aus der Sammlung abrufen und in eine Liste speichern
    docs = data_blick

    # TfidfVectorizer-Objekt initialisieren und auf den Text anwenden
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([doc['text'] for doc in docs])
    print(vectors.shape)


    duplicates = set()

    # Schwellenwert für die Ähnlichkeit festlegen
    threshold = 0.90

    # Cosine-Similaritätsmatrix berechnen
    for i,v in enumerate(vectors):
        cosine_sim = cosine_similarity(vectors, v)
        # print(cosine_sim)
        # break
        for j in range(i+1, len(cosine_sim)):
            if cosine_sim[j][0] > threshold:
                duplicates.add(j)

    # Eindeutige Dokumente auswählen
    unique_docs_watson = []
    for i in range(len(docs)):
        if i not in duplicates:
            unique_docs_watson.append(docs[i])

    print(f'unique docs {source}: {len(unique_docs_watson)}')


    # Als JSON abspeichern

    df = pd.DataFrame(unique_docs_watson)

    records = df.to_dict('records')

    # Datensätze in eine JSON-Datei schreiben
    with open(f'clean-data_{source}_cosine.json', 'w', encoding='utf8') as file:
        json.dump(records, file)


if __name__ == '__main__':
    file_name = sys.argv[1]
    source = sys.argv[2];

    print("Starting export of clean articles")
    print(f"file_name: {file_name}")
    print(f"source", source)
    export_clean_articles(file_name, source)