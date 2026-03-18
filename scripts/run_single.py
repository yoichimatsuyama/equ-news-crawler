#!/usr/bin/env python3
"""Simple runner to fetch a single Engoo article, parse it, and save JSON + Markdown output."""
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, UTC

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.scraper.content_fetcher import fetch_article_html
from src.parser.html_parser import parse_article
from src.builder.json_builder import build_output_stem, to_json_bytes
from src.builder.md_builder import to_markdown

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Fetch and convert a single Engoo article')
    parser.add_argument('url', help='Article URL')
    parser.add_argument('--out', default='output/articles', help='Output base directory')
    parser.add_argument('--headless', action='store_true', help='Run Playwright in headless mode')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    html = fetch_article_html(args.url, headless=args.headless)
    parsed = parse_article(html, args.url)

    # add scraped_at timestamp
    now = datetime.now(UTC)
    parsed['meta']['scraped_at'] = now.isoformat().replace('+00:00', 'Z')

    stem = build_output_stem(parsed['id'], parsed['meta'].get('title') or parsed['id'])
    month_dir = now.strftime('%Y-%m')

    # JSON output
    json_dir = Path(args.out) / 'json' / month_dir
    json_dir.mkdir(parents=True, exist_ok=True)
    json_path = json_dir / f"{stem}.json"
    json_path.write_bytes(to_json_bytes(parsed))
    logger.info('Saved %s', json_path)

    # Markdown output
    md_dir = Path(args.out) / 'md' / month_dir
    md_dir.mkdir(parents=True, exist_ok=True)
    md_path = md_dir / f"{stem}.md"
    md_path.write_text(to_markdown(parsed), encoding='utf-8')
    logger.info('Saved %s', md_path)


if __name__ == '__main__':
    main()
