# pylint: disable=line-too-long
"""
Use this module to test the url_extractor.
It can extract links from a html file

USAGE:
- python -m path.to.folder
- python -m path.to.folder path/to/file.html https://online-link.to/that/html/file
- python -m gender_gap_tracker.utils.url_extractor test/watson.html "https://www.watson.ch/sport/fussball/543816839-wm-2022-infantino-zeigt-auf-foto-auf-umstrittene-one-love-binde"
"""
# pylint: enable=line-too-long

if __name__ == "__main__":
    import sys
    from functools import reduce
    from time import time
    from .url_extractor import get_all_urls_from_html

    HTML_FILE = "test/64332edcfa7642fa86fe6cdb0757b27e.html"
    # pylint: disable=line-too-long
    PAGE_URL = "https://www.srf.ch/unternehmen/einfuehrung-programmprofile-und-sendungskosten-2021-bei-srf"
    # pylint: enable=line-too-long

    if len(sys.argv) > 2:
        HTML_FILE = sys.argv[1]
        PAGE_URL = sys.argv[2]

    start_time = time()
    all_urls_from_variable = get_all_urls_from_html(
        HTML_FILE,
        PAGE_URL,
    )
    end_time = time()

    print()
    print(f"Found {len(all_urls_from_variable)} urls:")
    print(reduce(lambda a, b: a + "\n" + b, all_urls_from_variable))

    print()
    print(f"Execution time: {end_time - start_time}")
