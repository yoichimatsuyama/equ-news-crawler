"""Fetch article list from the Engoo internal API with pagination."""
import base64
import json
import logging
import re
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Dict, List

from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

INDEX_URL = "https://engoo.jp/app/daily-news"
BASE_URL = "https://engoo.jp"
CATEGORY_ID = "0225ae09-5d63-41c2-bd75-693985d07d78"
BRAND_ID = "cc234eaf-cd5d-4394-b94d-b8aabf3d5575"
API_PAGE_SIZE = 200


@dataclass
class ArticleEntry:
    """Metadata for a single article extracted from the API."""
    article_id: str
    url: str
    title: str
    title_ja: str | None = None
    level: str | None = None
    category: str | None = None
    published_date: str | None = None  # YYYY-MM-DD
    thumbnail_url: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _uuid_to_url_id(uuid_str: str) -> str:
    """Convert a UUID string to the base64url-encoded ID used in Engoo URLs."""
    return base64.urlsafe_b64encode(uuid.UUID(uuid_str).bytes).rstrip(b'=').decode()


def _title_to_slug(title: str) -> str:
    """Convert article title to URL slug matching Engoo's convention."""
    slug = title.lower()
    slug = re.sub(r"[''']", "", slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def _content_level_to_label(level: int) -> str:
    if level <= 3:
        return "Beginner"
    elif level <= 6:
        return "Intermediate"
    else:
        return "Advanced"


def _parse_api_items(items: list) -> List[ArticleEntry]:
    """Convert raw API response items to ArticleEntry objects."""
    entries = []
    for item in items:
        master_id = item.get('master_id')
        if not master_id:
            continue

        title_obj = item.get('title_text', {})
        title = title_obj.get('text', '')
        if not title:
            continue

        # Japanese title from translations
        title_ja = None
        for tr in title_obj.get('text_translations', []):
            if tr.get('language') == 'ja':
                title_ja = tr.get('translation')
                break

        url_id = _uuid_to_url_id(master_id)
        slug = _title_to_slug(title)
        url = f"{BASE_URL}/app/daily-news/article/{slug}/{url_id}"

        # Published date
        published_at = item.get('first_published_at')
        published_date = published_at[:10] if published_at else None

        # Level
        content_level = item.get('content_level')
        level = _content_level_to_label(content_level) if content_level else None

        # Thumbnail
        image = item.get('image') or {}
        thumbnail_url = image.get('url')

        entries.append(ArticleEntry(
            article_id=url_id,
            url=url,
            title=title,
            title_ja=title_ja,
            level=level,
            published_date=published_date,
            thumbnail_url=thumbnail_url,
        ))

    return entries


_FETCH_JS_TEMPLATE = '''async (params) => {{
    const baseUrl = "https://api.engoo.com/api/lesson_headers";
    let allItems = [];
    let start = params.start || 0;
    let lastPage = false;

    while (!lastPage) {{
        const qp = new URLSearchParams({{
            category: "{category}",
            direction: "desc",
            for_brand: "{brand}",
            order: "first_published_at",
            page_size: String({page_size}),
            type: "Published",
            published_latest: "true",
            min_level: "1",
            max_level: "9",
            start: String(start),
        }});
        const resp = await fetch(baseUrl + "?" + qp.toString());
        if (!resp.ok) throw new Error("API error: " + resp.status);
        const data = await resp.json();
        const items = data.data || [];
        allItems = allItems.concat(items);
        lastPage = data.meta?.pagination?.last_page ?? true;
        start += items.length;
        if (items.length === 0) break;
        if (params.limit && allItems.length >= params.limit) {{
            allItems = allItems.slice(0, params.limit);
            break;
        }}
    }}
    return allItems;
}}'''


def fetch_article_list(
    headless: bool = True,
    limit: int | None = None,
) -> List[ArticleEntry]:
    """Fetch article list via internal API using Playwright for auth context.

    Args:
        headless: Run browser in headless mode.
        limit: Maximum number of articles to fetch (None = all).

    Returns:
        List of ArticleEntry objects, newest first.
    """
    js_code = _FETCH_JS_TEMPLATE.format(
        category=CATEGORY_ID,
        brand=BRAND_ID,
        page_size=API_PAGE_SIZE,
    )

    logger.info("Fetching article list via API (limit=%s)", limit or "all")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(INDEX_URL, timeout=30000)
        page.wait_for_timeout(2000)

        raw_items = page.evaluate(js_code, {'limit': limit or 0})
        browser.close()

    entries = _parse_api_items(raw_items)
    logger.info("Fetched %d articles from API", len(entries))
    return entries
