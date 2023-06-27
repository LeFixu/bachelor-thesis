from .crawling.crawlers.srf.parsing import parse_article_or_news_ticker
from .aggregation.functions.get_citations_from_article import get_citations_from_article
from requests import get

print("Test")

if __name__ == "__main__":
    while True:
        print("Enter URL from srf.ch")

        url = input("URL: ")
        print(url)
        response = get(url, timeout=10)

        path_to_file = "article.html"
        with open(path_to_file, 'w', encoding='utf8') as fp:
            fp.write(response.text)
        
        print(f"Wrote {len(response.text)} characters to file.")

        article = parse_article_or_news_ticker(path_to_file, url)
        print(article["title"])

        citations = get_citations_from_article(article["text"])
        print(citations)

