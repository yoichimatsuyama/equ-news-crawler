# Engoo Daily News Extractor

A tool that automatically fetches articles from [Engoo Daily News](https://engoo.jp/app/daily-news) and saves them as structured JSON / Markdown files.

## Features

- Renders SPA pages via Playwright headless browser
- Parses Exercises 1–4 from each article into structured data
  - **Exercise 1** — Vocabulary (word, phonetics, part of speech, definition, example / with Japanese translations)
  - **Exercise 2** — Article (body text split into paragraphs)
  - **Exercise 3** — Discussion (list of questions)
  - **Exercise 4** — Further Discussion (list of questions)
- Article index retrieval via internal API (10,200+ articles, with pagination)
- Dual output in JSON + Markdown
- Duplicate prevention for already-fetched articles (idempotency)
- 5-second rate limiting between requests

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install
```

## Usage

### Single article

```bash
python scripts/run_single.py <article-url>
```

```bash
# Example
python scripts/run_single.py https://engoo.jp/app/daily-news/article/jr-east-to-raise-ticket-prices-for-first-time-in-39-years/I3UqCh1QEfGwqbdULhDSaQ
```

### Batch processing

```bash
# Process all unfetched articles from the latest 200 in the index
python scripts/run_batch.py --fetch-limit 200

# Process up to 10 new articles from the latest 50
python scripts/run_batch.py --fetch-limit 50 --limit 10

# Fetch the full index and process all articles (10,200+)
python scripts/run_batch.py
```

| Option | Description | Default |
|---|---|---|
| `--fetch-limit N` | Number of articles to retrieve from the API index | all |
| `--limit N` | Max number of unfetched articles to process | all |
| `--out DIR` | Output base directory | `output/articles` |
| `--headless` | Run browser in headless mode | off |

## Output

```
output/articles/
├── json/{YYYY-MM}/{id}_{YYYYMMDD}_{slug}.json
├── md/{YYYY-MM}/{id}_{YYYYMMDD}_{slug}.md
└── ../fetched_ids.json   # Fetched article IDs (for duplicate prevention)
```

## Project Structure

```
src/
├── scraper/
│   ├── content_fetcher.py   # Fetch article HTML via Playwright
│   └── index_scraper.py     # Fetch article list via internal API
├── parser/
│   └── html_parser.py       # HTML → structured data conversion
├── builder/
│   ├── json_builder.py      # JSON output
│   └── md_builder.py        # Markdown output
├── storage/
│   └── fetched_tracker.py   # Fetched ID tracking
├── pipeline.py              # Batch pipeline orchestration
└── config.py                # Configuration constants
scripts/
├── run_single.py            # Single article fetch script
└── run_batch.py             # Batch fetch script
spec/
├── PRD_Engoo_Daily_News_Extractor_EN.md
└── PRD_Engoo_Daily_News_Extractor_JP.md
```

## Tech Stack

| Layer | Technology |
|---|---|
| Scraping | Playwright (Python) |
| HTML Parsing | BeautifulSoup4 + lxml |
| Runtime | Python 3.11+ |
