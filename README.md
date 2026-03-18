# Engoo Daily News Extractor — Phase 1 PoC

This repository contains Phase 1 proof-of-concept code for fetching a single Engoo Daily News article (rendered via Playwright), parsing the Exercises (vocabulary, article body, discussion), and producing a JSON file following the PRD schema.

Quick setup (macOS / Linux):

1. Create and activate a virtualenv:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies and Playwright browsers:

```bash
pip install -r requirements.txt
playwright install
```

3. Run the single-article fetch PoC:

```bash
python scripts/run_single.py https://engoo.jp/app/daily-news/articles/example-id
```

Output JSON will be saved under `output/articles/{YYYY-MM}/`.

Notes:
- This is a Phase 1 PoC. Parsers are intentionally resilient and conservative; adjust selectors as needed for real pages.
