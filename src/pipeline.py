"""Batch pipeline: fetch index, then process each article with rate limiting."""
import logging
import time
from pathlib import Path
from datetime import datetime, UTC
from typing import List

from src.scraper.index_scraper import ArticleEntry, fetch_article_list
from src.scraper.content_fetcher import fetch_article_html
from src.parser.html_parser import parse_article
from src.builder.json_builder import build_output_stem, to_json_bytes
from src.builder.md_builder import to_markdown
from src.storage.fetched_tracker import FetchedTracker
from src.config import MIN_REQUEST_INTERVAL

logger = logging.getLogger(__name__)


def _save_article(parsed: dict, out_base: Path) -> None:
    """Save a parsed article as both JSON and Markdown."""
    stem = build_output_stem(
        parsed['id'],
        parsed['meta'].get('title') or parsed['id'],
        parsed['meta'].get('published_date'),
    )
    pub_date = parsed['meta'].get('published_date')
    if pub_date:
        month_dir = pub_date[:7]  # YYYY-MM
    else:
        month_dir = datetime.now(UTC).strftime('%Y-%m')

    # JSON
    json_dir = out_base / 'json' / month_dir
    json_dir.mkdir(parents=True, exist_ok=True)
    json_path = json_dir / f"{stem}.json"
    json_path.write_bytes(to_json_bytes(parsed))
    logger.info("Saved %s", json_path)

    # Markdown
    md_dir = out_base / 'md' / month_dir
    md_dir.mkdir(parents=True, exist_ok=True)
    md_path = md_dir / f"{stem}.md"
    md_path.write_text(to_markdown(parsed), encoding='utf-8')
    logger.info("Saved %s", md_path)


def run_batch(
    out_base: Path = Path("output/articles"),
    headless: bool = True,
    limit: int | None = None,
    fetch_limit: int | None = None,
) -> dict:
    """Run the full batch pipeline.

    Args:
        out_base: Output base directory.
        headless: Run browser in headless mode.
        limit: Max number of new (unfetched) articles to process.
        fetch_limit: Max number of articles to retrieve from the API index.
            Use this to avoid fetching all 10,000+ articles when not needed.

    Returns a summary dict with counts of processed/skipped/failed articles.
    """
    tracker = FetchedTracker()
    interval = MIN_REQUEST_INTERVAL.total_seconds()

    # Step 1: Fetch article list via API
    entries = fetch_article_list(headless=headless, limit=fetch_limit)
    logger.info("Found %d articles via API", len(entries))

    # Filter out already-fetched articles
    new_entries = [e for e in entries if not tracker.is_fetched(e.article_id)]
    skipped = len(entries) - len(new_entries)
    if skipped:
        logger.info("Skipping %d already-fetched articles", skipped)

    if limit is not None:
        new_entries = new_entries[:limit]

    logger.info("Will process %d new articles", len(new_entries))

    # Step 2: Process each article
    success = 0
    failed = 0
    failed_ids: List[str] = []

    for i, entry in enumerate(new_entries):
        logger.info(
            "[%d/%d] Processing: %s", i + 1, len(new_entries), entry.title
        )

        try:
            html = fetch_article_html(entry.url, headless=headless)
            parsed = parse_article(html, entry.url)

            # Supplement metadata from index page
            meta = parsed['meta']
            now = datetime.now(UTC)
            meta['scraped_at'] = now.isoformat().replace('+00:00', 'Z')
            if entry.published_date and not meta['published_date']:
                meta['published_date'] = entry.published_date
            if entry.category and not meta['category']:
                meta['category'] = entry.category
            if entry.thumbnail_url and not meta['thumbnail_url']:
                meta['thumbnail_url'] = entry.thumbnail_url
            if entry.title_ja and not meta['title_ja']:
                meta['title_ja'] = entry.title_ja

            _save_article(parsed, out_base)
            tracker.mark_fetched(entry.article_id)
            success += 1

        except Exception:
            logger.exception("Failed to process %s", entry.url)
            failed += 1
            failed_ids.append(entry.article_id)

        # Rate limiting: wait between requests
        if i < len(new_entries) - 1:
            logger.debug("Waiting %.1fs before next request", interval)
            time.sleep(interval)

    summary = {
        'total_on_index': len(entries),
        'skipped': skipped,
        'processed': success,
        'failed': failed,
        'failed_ids': failed_ids,
    }
    logger.info(
        "Batch complete: %d processed, %d skipped, %d failed",
        success, skipped, failed,
    )
    return summary
