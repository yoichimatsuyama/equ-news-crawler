#!/usr/bin/env python3
"""Batch runner: fetch article index and process all new articles."""
import sys
import argparse
import logging
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import run_batch

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Batch fetch and convert Engoo Daily News articles'
    )
    parser.add_argument(
        '--out', default='output/articles',
        help='Output base directory (default: output/articles)',
    )
    parser.add_argument(
        '--limit', type=int, default=None,
        help='Max number of new articles to process (default: all)',
    )
    parser.add_argument(
        '--fetch-limit', type=int, default=None,
        help='Max number of articles to retrieve from API index (default: all ~10,000+)',
    )
    parser.add_argument(
        '--headless', action='store_true',
        help='Run Playwright in headless mode',
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )

    summary = run_batch(
        out_base=Path(args.out),
        headless=args.headless,
        limit=args.limit,
        fetch_limit=args.fetch_limit,
    )

    print()
    print("=== Batch Summary ===")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
