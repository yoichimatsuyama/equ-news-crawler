import json
from datetime import datetime
from typing import Dict
import re


def _slugify(text: str) -> str:
    text = text or ''
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip('-')
    return text or 'article'


def build_output_stem(article_id: str, title: str, published_date: str = None) -> str:
    date = datetime.utcnow().strftime('%Y%m%d')
    if published_date:
        date = published_date.replace('-', '')
    slug = _slugify(title)
    return f"{article_id}_{date}_{slug}"


def build_output_filename(article_id: str, title: str, published_date: str = None) -> str:
    return build_output_stem(article_id, title, published_date) + ".json"


def to_json_bytes(obj: Dict) -> bytes:
    return json.dumps(obj, ensure_ascii=False, indent=2).encode('utf-8')
