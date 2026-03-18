# PRD: Engoo Daily News Content Extraction & JSON Conversion System

**Document No.:** PRD-ENGOO-001  
**Version:** 1.0  
**Created:** 2026-03-18  
**Status:** Draft

---

## 1. Overview & Objectives

### 1.1 Project Summary

Build a system that automatically retrieves English-learning articles from Engoo Daily News (`https://engoo.jp/app/daily-news`) and stores each article's structured content as a JSON file.

### 1.2 Background & Motivation

Engoo Daily News is a daily-updated English learning resource, but the following limitations currently exist.

- Content is browser-only, making programmatic reuse and analysis difficult
- Vocabulary items, article body, and discussion questions are not machine-readable in their current form
- There is a need to automate content supply for English dialogue assessment systems such as LANGX and EQU AI

### 1.3 Goals

1. Automatically fetch and structure all article content from Engoo Daily News
2. Parse each article at the Exercise level and store it as one JSON file per article
3. Build a pipeline that continuously accumulates new articles via scheduled execution

---

## 2. Scope

### 2.1 Target Content

| Field | Description |
|---|---|
| Title | Article headline (English) |
| Level | Difficulty label (Beginner / Intermediate / Advanced, etc.) |
| Exercise 1 | Vocabulary (word list: term, phonetics, part of speech, definition, example sentence) |
| Exercise 2 | Article (news article body text) |
| Exercise 3 | Discussion (discussion questions) |
| Exercise 4 | Further Discussion (extended discussion questions) |

### 2.2 Target URLs

- Index page: `https://engoo.jp/app/daily-news`
- Individual articles: `https://engoo.jp/app/daily-news/articles/{article_id}` (inferred pattern)
- English version reference: `https://engoo.com/app/lessons/newspapers/{lesson_id}`

### 2.3 Out of Scope

- Audio file retrieval (deferred to a later phase)
- Image content download (deferred to a later phase)
- Premium content requiring an Engoo account login

---

## 3. Users & Use Cases

### 3.1 Primary Users

| User | Purpose |
|---|---|
| LANGX Development Team | Use articles as training data and evaluation material for English learning |
| EQU Copilot Development Team | Use as conversation scenario material for PoC |
| AI Researchers (Applied Research Unit) | Use as analytical data for vocabulary and discourse structure |

### 3.2 Use Cases

**Scenario A: Scheduled Daily Batch**  
Automatically runs every day at 7:00 AM. Detects newly published articles for the day, generates JSON files, and saves them to the designated storage (e.g., GCS).

**Scenario B: Bulk Backfill**  
On first run, retrieves and converts all previously published articles (or a specified date range).

**Scenario C: Manual Single-Article Fetch**  
Given a specific article ID or URL, immediately fetches and converts a single article.

---

## 4. Technical Assumptions & Constraints

### 4.1 Technical Challenges

Engoo Daily News is built as a **JavaScript SPA (Single Page Application)**, which means standard HTTP requests cannot retrieve content (`Please enable JavaScript to view this page.` is returned instead).

One of the following approaches is therefore required.

| Approach | Method | Difficulty | Stability |
|---|---|---|---|
| **A. Headless Browser** | Playwright / Puppeteer | Medium | High |
| **B. Internal API Analysis** | Analyze XHR/Fetch traffic via Chrome DevTools and call the API endpoint directly | High | High (if endpoint identified) |
| **C. Official Engoo API** | Review official documentation and apply for access | Low (process required) | Highest |

**Recommendation: Default to Approach A (Playwright), with Approach B (Internal API) implemented as a supplementary fast path.**

### 4.2 Terms of Service & Ethical Considerations

- Review of Engoo's Terms of Service is mandatory before proceeding
- Respect `robots.txt` (minimum crawl interval: 5 seconds or more)
- Retrieved data must be restricted to internal product development and research purposes; redistribution is prohibited

---

## 5. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Engoo Extractor Pipeline                │
│                                                         │
│  ┌──────────┐   ┌──────────────┐   ┌────────────────┐  │
│  │ Scheduler│──▶│ ArticleIndex │──▶│ ContentFetcher │  │
│  │(cron/GCS)│   │  Scraper     │   │  (Playwright)  │  │
│  └──────────┘   └──────────────┘   └───────┬────────┘  │
│                                            │            │
│                                    ┌───────▼────────┐  │
│                                    │  HTML Parser   │  │
│                                    │ (BeautifulSoup │  │
│                                    │  + regex)      │  │
│                                    └───────┬────────┘  │
│                                            │            │
│                                    ┌───────▼────────┐  │
│                                    │  JSON Builder  │  │
│                                    │  & Validator   │  │
│                                    └───────┬────────┘  │
│                                            │            │
│                                    ┌───────▼────────┐  │
│                                    │    Storage     │  │
│                                    │  (GCS / Local) │  │
│                                    └────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 5.1 Component Descriptions

| Component | Role |
|---|---|
| **Scheduler** | Periodic execution trigger via cron or Cloud Scheduler |
| **ArticleIndexScraper** | Retrieves the list of article IDs from the index page |
| **ContentFetcher** | Loads each article page and captures rendered HTML via Playwright |
| **HTMLParser** | Extracts content from retrieved HTML at the Exercise level |
| **JSONBuilder** | Converts parsed results into the defined schema and validates them |
| **Storage** | Saves output to a GCS bucket or local filesystem |

---

## 6. JSON Schema Specification

### 6.1 Output File Naming Convention

```
{article_id}_{YYYYMMDD}_{slug}.json
Example: BttvaDsYEeet95PQUY-xEA_20260318_ai-robot-new-friend.json
```

### 6.2 JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "EngooArticle",
  "type": "object",
  "required": ["id", "meta", "exercises"],
  "properties": {
    "id": {
      "type": "string",
      "description": "Unique identifier for the Engoo article"
    },
    "meta": {
      "type": "object",
      "required": ["title", "level", "url", "scraped_at", "published_date"],
      "properties": {
        "title":          { "type": "string" },
        "title_ja":       { "type": ["string", "null"], "description": "Japanese title, if available" },
        "level":          { "type": "string", "enum": ["Beginner", "Intermediate", "Advanced", "Unknown"] },
        "category":       { "type": ["string", "null"], "description": "Article category (e.g. Science, Health)" },
        "url":            { "type": "string", "format": "uri" },
        "thumbnail_url":  { "type": ["string", "null"] },
        "published_date": { "type": ["string", "null"], "description": "Format: YYYY-MM-DD" },
        "scraped_at":     { "type": "string", "description": "Fetch timestamp in ISO 8601 format" }
      }
    },
    "exercises": {
      "type": "object",
      "properties": {
        "exercise_1_vocabulary": {
          "type": "object",
          "properties": {
            "label": { "type": "string", "example": "Vocabulary" },
            "items": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["word"],
                "properties": {
                  "word":           { "type": "string" },
                  "phonetics":      { "type": ["string", "null"], "description": "Phonetic transcription" },
                  "part_of_speech": { "type": ["string", "null"], "description": "Part of speech (noun, verb, etc.)" },
                  "definition":     { "type": "string" },
                  "example":        { "type": ["string", "null"] }
                }
              }
            }
          }
        },
        "exercise_2_article": {
          "type": "object",
          "properties": {
            "label":      { "type": "string", "example": "Article" },
            "body":       { "type": "string", "description": "Full article body with paragraphs separated by \\n" },
            "paragraphs": {
              "type": "array",
              "items": { "type": "string" },
              "description": "Article body split into individual paragraph strings"
            }
          }
        },
        "exercise_3_discussion": {
          "type": "object",
          "properties": {
            "label":     { "type": "string", "example": "Discussion" },
            "questions": {
              "type": "array",
              "items": { "type": "string" }
            }
          }
        },
        "exercise_4_further_discussion": {
          "type": "object",
          "properties": {
            "label":     { "type": "string", "example": "Further Discussion" },
            "questions": {
              "type": "array",
              "items": { "type": "string" }
            }
          }
        }
      }
    }
  }
}
```

### 6.3 Sample Output JSON

```json
{
  "id": "BttvaDsYEeet95PQUY-xEA",
  "meta": {
    "title": "AI Robot Becomes New Friend for Lonely Elderly",
    "title_ja": null,
    "level": "Intermediate",
    "category": "Science & Technology",
    "url": "https://engoo.jp/app/daily-news/articles/BttvaDsYEeet95PQUY-xEA",
    "thumbnail_url": "https://cdn.engoo.com/images/abc123.jpg",
    "published_date": "2026-03-18",
    "scraped_at": "2026-03-18T07:05:00+09:00"
  },
  "exercises": {
    "exercise_1_vocabulary": {
      "label": "Vocabulary",
      "items": [
        {
          "word": "companion",
          "phonetics": "/kəmˈpænjən/",
          "part_of_speech": "noun",
          "definition": "a person or animal you spend a lot of time with",
          "example": "The dog was her faithful companion for 12 years."
        }
      ]
    },
    "exercise_2_article": {
      "label": "Article",
      "body": "Paragraph one text here.\n\nParagraph two text here.",
      "paragraphs": [
        "Paragraph one text here.",
        "Paragraph two text here."
      ]
    },
    "exercise_3_discussion": {
      "label": "Discussion",
      "questions": [
        "What do you think about AI companions for elderly people?",
        "Have you ever felt lonely? What did you do?"
      ]
    },
    "exercise_4_further_discussion": {
      "label": "Further Discussion",
      "questions": [
        "Should governments invest in AI care robots? Why or why not?",
        "What are the potential risks of relying on AI for emotional support?"
      ]
    }
  }
}
```

---

## 7. Functional Requirements

### 7.1 Must Have

| ID | Requirement |
|---|---|
| F-01 | Must be able to retrieve a list of article IDs from the index page |
| F-02 | Must be able to capture fully rendered HTML for each article page using Playwright |
| F-03 | Must be able to extract Exercises 1–4 individually and produce schema-compliant JSON |
| F-04 | Must track already-fetched article IDs and skip duplicates (idempotency) |
| F-05 | Must save JSON files to local storage or GCS following the naming convention |
| F-06 | Must log errors on fetch failure and perform retry processing |

### 7.2 Should Have

| ID | Requirement |
|---|---|
| F-07 | Selective fetch by level filter (e.g., Beginner only) |
| F-08 | Selective fetch by category filter |
| F-09 | Bulk fetch mode for retrieving articles within a specified date range |
| F-10 | Output quality assurance via JSON schema validation (e.g., jsonschema) |
| F-11 | Summary report output showing progress (count, success/failure, elapsed time) |

### 7.3 Nice to Have

| ID | Requirement |
|---|---|
| F-12 | Fast fetch mode via internal API (XHR/Fetch) analysis |
| F-13 | Audio file URL retrieval and storage |
| F-14 | Automatic conversion of retrieved data into the LANGX assessment schema |
| F-15 | Serverless scheduled execution via Cloud Run + Cloud Scheduler |

---

## 8. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Performance** | Fetch and conversion per article: within 30 seconds |
| **Throughput** | Maximum 3 parallel workers (to limit server load) |
| **Request Interval** | Minimum 5 seconds between requests (robots.txt compliance and throttling) |
| **Availability** | Auto-retry on batch failure (up to 3 retries with exponential backoff) |
| **Data Integrity** | Lock management on fetched IDs to prevent duplicate retrieval in parallel execution |
| **Storage** | Approx. 10–50 KB per JSON file (estimated annual volume: ~18 MB/year) |
| **Logging** | Fetch timestamp, article ID, and status saved as structured logs (JSON Lines) |

---

## 9. Implementation Stack (Recommended)

| Layer | Technology | Rationale |
|---|---|---|
| Scraping | **Playwright (Python)** | SPA-compatible, stable headless operation |
| HTML Parsing | **BeautifulSoup4 + lxml** | Fast, widely adopted |
| Schema Validation | **jsonschema** | Draft-07 compliant |
| Storage | **Google Cloud Storage** | Integration with existing GCP infrastructure |
| Scheduler | **Cloud Scheduler + Cloud Run Jobs** | Serverless, low cost |
| Log Management | **Google Cloud Logging** | Integration with existing infrastructure |
| Runtime | **Python 3.11+** | Team standard |

---

## 10. Directory Structure

```
engoo-extractor/
├── README.md
├── pyproject.toml
├── .env.example
├── src/
│   ├── __init__.py
│   ├── config.py              # Environment variables and configuration
│   ├── scraper/
│   │   ├── index_scraper.py   # Article index fetcher
│   │   └── content_fetcher.py # Playwright article fetcher
│   ├── parser/
│   │   ├── html_parser.py     # HTML → structured data conversion
│   │   └── exercise_parser.py # Per-exercise parsers
│   ├── builder/
│   │   ├── json_builder.py    # JSON schema conversion
│   │   └── validator.py       # Schema validation
│   ├── storage/
│   │   ├── local_storage.py
│   │   └── gcs_storage.py
│   └── pipeline.py            # Main pipeline orchestration
├── tests/
│   ├── fixtures/              # Sample HTML for testing
│   ├── test_parser.py
│   └── test_builder.py
├── scripts/
│   ├── run_daily.sh           # Daily batch execution script
│   └── run_bulk.sh            # Bulk fetch script
└── output/                    # Local output directory (.gitignore)
    └── articles/
        └── {YYYY-MM}/
            └── {article_id}.json
```

---

## 11. Error Handling Specification

| Error Type | Handling |
|---|---|
| Page load timeout | 30-second timeout; retry up to 3 times |
| HTML parse failure (element not found) | Store `null` value + emit warning log |
| JSON validation failure | Skip file save + error log + Slack alert |
| Network error | Retry with exponential backoff (5s → 15s → 45s) |
| Rate limiting (HTTP 429) | Wait 60 seconds before retrying |
| Storage write failure | Fall back to local storage |

---

## 12. Acceptance Criteria

| AC | Criterion |
|---|---|
| AC-01 | Given a target article URL, a JSON file containing all fields for Exercises 1–4 is generated |
| AC-02 | Every vocabulary item in Exercise 1 contains at minimum `word` and `definition` |
| AC-03 | The article body in Exercise 2 is split into a `paragraphs` array at the paragraph level |
| AC-04 | The number of questions in Exercise 3 and Exercise 4 matches the actual content on the page |
| AC-05 | Running the pipeline twice on the same article does not produce duplicate JSON files (idempotency) |
| AC-06 | Schema validation pass rate of 95% or higher across 100 articles |

---

## 13. Phase Plan

| Phase | Scope | Estimated Duration |
|---|---|---|
| **Phase 1** | Playwright environment setup + single-article fetch and parse PoC | 2 days |
| **Phase 2** | Article index fetching + batch processing + GCS storage | 3 days |
| **Phase 3** | Schema validation + error handling + logging | 2 days |
| **Phase 4** | Cloud Run scheduled execution + Slack alert integration | 2 days |
| **Phase 5** | Historical bulk fetch mode | 1 day |

---

## 14. Open Questions & Risks

| Item | Description | Mitigation |
|---|---|---|
| **Terms of Service Review** | Explicit confirmation of scraping permissibility is not yet complete | Contact Engoo directly or conduct a thorough ToS review |
| **DOM Structure Change Risk** | If Engoo updates its frontend, parsers may break | Run parser tests periodically + configure alerts |
| **Authentication Requirements** | If some content requires login, session management will be needed | Implement cookie-based session injection |
| **Internal API Identification** | It is unconfirmed whether direct API access via XHR analysis is feasible | Investigate in parallel during the Phase 1 PoC |

---

*This PRD is for internal development use at Equmenopolis, Inc. External distribution is prohibited.*
