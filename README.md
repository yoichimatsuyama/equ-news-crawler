# Engoo Daily News Extractor

[Engoo Daily News](https://engoo.jp/app/daily-news) の記事を自動取得し、構造化された JSON / Markdown ファイルとして保存するツール。

## 機能

- Playwright によるヘッドレスブラウザで SPA ページをレンダリング・取得
- 記事ごとに Exercise 1〜4 を構造化パース
  - **Exercise 1** — Vocabulary（単語・発音・品詞・定義・例文 / 日本語訳付き）
  - **Exercise 2** — Article（本文パラグラフ分割）
  - **Exercise 3** — Discussion（質問リスト）
  - **Exercise 4** — Further Discussion（質問リスト）
- 内部 API によるインデックス取得（全 10,200+ 件、ページネーション対応）
- JSON + Markdown の同時出力
- 取得済み記事の重複防止（idempotency）
- 5秒間隔のレートリミット

## セットアップ

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install
```

## 使い方

### 単一記事の取得

```bash
python scripts/run_single.py <記事URL>
```

```bash
# 例
python scripts/run_single.py https://engoo.jp/app/daily-news/article/jr-east-to-raise-ticket-prices-for-first-time-in-39-years/I3UqCh1QEfGwqbdULhDSaQ
```

### バッチ取得

```bash
# 最新200件のインデックスから未取得分を全て処理
python scripts/run_batch.py --fetch-limit 200

# 最新50件から最大10件を処理
python scripts/run_batch.py --fetch-limit 50 --limit 10

# 全記事のインデックスを取得して処理（10,200+件）
python scripts/run_batch.py
```

| オプション | 説明 | デフォルト |
|---|---|---|
| `--fetch-limit N` | API から取得するインデックスの件数 | 全件 |
| `--limit N` | 実際に処理する未取得記事の件数 | 全件 |
| `--out DIR` | 出力ベースディレクトリ | `output/articles` |
| `--headless` | ブラウザを非表示で実行 | off |

## 出力

```
output/articles/
├── json/{YYYY-MM}/{id}_{YYYYMMDD}_{slug}.json
├── md/{YYYY-MM}/{id}_{YYYYMMDD}_{slug}.md
└── ../fetched_ids.json   # 取得済み記事ID（重複防止用）
```

## プロジェクト構成

```
src/
├── scraper/
│   ├── content_fetcher.py   # Playwright による記事HTML取得
│   └── index_scraper.py     # 内部API経由の記事一覧取得
├── parser/
│   └── html_parser.py       # HTML → 構造化データ変換
├── builder/
│   ├── json_builder.py      # JSON出力
│   └── md_builder.py        # Markdown出力
├── storage/
│   └── fetched_tracker.py   # 取得済みID管理
├── pipeline.py              # バッチパイプライン
└── config.py                # 設定定数
scripts/
├── run_single.py            # 単一記事取得スクリプト
└── run_batch.py             # バッチ取得スクリプト
spec/
├── PRD_Engoo_Daily_News_Extractor_EN.md
└── PRD_Engoo_Daily_News_Extractor_JP.md
```

## 技術スタック

| レイヤー | 技術 |
|---|---|
| スクレイピング | Playwright (Python) |
| HTMLパース | BeautifulSoup4 + lxml |
| ランタイム | Python 3.11+ |
