"""This module exports the articles collection from our MongoDB to a JSON file."""
import json
from datetime import datetime
from ..utils.db_driver.db_driver import get_articles

data = get_articles()

date_as_string = datetime.today().strftime('%Y%m%d-%H%M')
file_name = f"./demo/crawling/db_backup/articles_{date_as_string}.json"

with open(file_name, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
