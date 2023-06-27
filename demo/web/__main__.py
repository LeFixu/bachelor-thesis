from flask import Flask, request, redirect, render_template
from os import path
import pathlib


from ..crawling.crawlers.srf.parsing import parse_article_or_news_ticker as parse_srf
from ..crawling.crawlers.zwanzig_min.parsing import parse_article_or_news_ticker as parse_blick
from ..crawling.crawlers.blick.parsing import parse_article_or_news_ticker as parse_20min
from ..crawling.crawlers.watson.crawler import analyze_web_page as parse_watson
from ..aggregation.functions.get_citations_from_article import get_citations_from_article
from requests import get

app = Flask(__name__,
            static_url_path='', 
            static_folder='static',
            template_folder='templates')

@app.route('/')
def index():
    return redirect("index.html", code=302)

@app.route('/submit', methods=['POST'])
def submit():
    text = request.form.get('text')
    # Do something with the input_text

    citations = get_citations_from_text(text)
    print(citations)
    return render_template('citations.html', citations=citations, text = text)


def get_citations_from_text(text: str):
    # response = get(text, timeout=10)
    
    # print(f"Wrote {len(response.text)} characters to file.")

    # if "www.srf.ch" in text:
    #     parse = parse_srf
    #     print("SRF Parser")
    # elif "www.blick.ch" in text:
    #     parse = parse_blick
    #     print("Blick Parser")
    # elif "www.20min.ch" in text:
    #     parse = parse_20min
    #     print("20min Parser")
    
    # if "www.watson.ch" in text:
    #     article = parse_watson(text)
    # else:
    #     path_to_file = "article.html"
    #     with open(path_to_file, 'w', encoding='utf8') as fp:
    #         fp.write(response.text)
    #     article = parse(path_to_file, text)

    # print(article["title"])

    # citations = get_citations_from_article(article["text"])
    citations = get_citations_from_article(text)
    print(citations)
    return citations


if __name__ == '__main__':
    app.run(debug=True)