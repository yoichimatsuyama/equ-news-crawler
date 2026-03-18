# PRD: Engoo Daily News コンテンツ抽出・JSON変換システム

**文書番号:** PRD-ENGOO-001  
**バージョン:** 1.0  
**作成日:** 2026-03-18  
**ステータス:** Draft

---

## 1. 概要・目的

### 1.1 プロジェクト概要

Engoo Daily News（`https://engoo.jp/app/daily-news`）に掲載される英語学習記事を自動取得し、各記事の構造化データをJSON形式で保存するシステムを構築する。

### 1.2 背景・動機

Engoo Daily Newsは毎日更新される英語学習コンテンツだが、以下の課題がある。

- Webブラウザ上での閲覧に限定されており、コンテンツの再利用・分析が困難
- 語彙・記事本文・設問が分散していて機械的に処理できない
- LANGX・EQU AIなどの英語対話評価システムへのコンテンツ供給を自動化したい

### 1.3 目標

1. Engoo Daily Newsの全記事コンテンツを自動取得・構造化する
2. 各記事をExercise単位でパースし、1記事 = 1 JSONファイルに保存する
3. 定期実行によって新着記事を継続的に蓄積できるパイプラインを構築する

---

## 2. スコープ

### 2.1 対象コンテンツ

| フィールド | 内容 |
|---|---|
| タイトル | 記事の見出し（英語） |
| レベル | 難易度表示（Beginner / Intermediate / Advanced など） |
| Exercise 1 | Vocabulary（語彙リスト：単語・発音・品詞・定義・例文） |
| Exercise 2 | Article（ニュース記事本文） |
| Exercise 3 | Discussion（ディスカッション設問） |
| Exercise 4 | Further Discussion（発展ディスカッション設問） |

### 2.2 対象URL

- トップ: `https://engoo.jp/app/daily-news`
- 個別記事: `https://engoo.jp/app/daily-news/articles/{article_id}`（推定パターン）
- 英語版も参照: `https://engoo.com/app/lessons/newspapers/{lesson_id}`

### 2.3 スコープ外

- 音声ファイルの取得（別フェーズ）
- 画像コンテンツのダウンロード（別フェーズ）
- Engooアカウント認証が必要なプレミアムコンテンツ

---

## 3. ユーザー・利用シナリオ

### 3.1 主要ユーザー

| ユーザー | 利用目的 |
|---|---|
| LANGX 開発チーム | 英語学習コンテンツをトレーニングデータ・評価素材として活用 |
| EQU Copilot 開発チーム | PoC用の会話シナリオ素材として活用 |
| AI研究者（Applied Research Unit） | 語彙・談話構造の分析データとして活用 |

### 3.2 利用シナリオ

**シナリオ A：定期バッチ取得**  
毎日 AM 7:00 に自動実行。当日公開の新着記事を検出し、JSONを生成して所定のストレージ（GCS等）に保存する。

**シナリオ B：過去記事の一括取得**  
初回実行時に公開済み記事を全件（または指定期間）遡って取得・変換する。

**シナリオ C：特定記事の手動取得**  
記事IDまたはURLを指定し、単一記事を即時取得・変換する。

---

## 4. 技術的前提・制約

### 4.1 技術的課題

Engoo Daily News は **JavaScript SPA（Single Page Application）** で構築されており、通常の HTTP リクエストではコンテンツを取得できない（`Please enable JavaScript to view this page.` が返される）。

このため、以下のいずれかのアプローチが必要。

| アプローチ | 手段 | 難易度 | 安定性 |
|---|---|---|---|
| **A. ヘッドレスブラウザ** | Playwright / Puppeteer | 中 | 高 |
| **B. 内部API解析** | Chrome DevToolsでXHR/Fetch通信を解析し、APIエンドポイントを直接叩く | 高 | 高（取得成功時） |
| **C. Engoo公式API** | 公式ドキュメント確認・申請 | 低（手続き必要） | 最高 |

**推奨：アプローチ A（Playwright）をデフォルトとし、B（内部API）を補助手段として実装。**

### 4.2 利用規約・倫理的考慮

- Engoo利用規約（Terms of Service）の確認が必須
- robots.txt を尊重した実装（クロール間隔：最低5秒以上）
- 取得データは自社製品の開発・研究目的に限定し、再配布禁止

---

## 5. システムアーキテクチャ

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

### 5.1 コンポーネント説明

| コンポーネント | 役割 |
|---|---|
| **Scheduler** | cronまたはCloud Schedulerによる定期実行トリガー |
| **ArticleIndexScraper** | 記事一覧ページから記事IDリストを取得 |
| **ContentFetcher** | Playwrightで各記事ページをロード・HTML取得 |
| **HTMLParser** | 取得HTMLからExercise単位でコンテンツを抽出 |
| **JSONBuilder** | パース結果を所定スキーマに変換・バリデーション |
| **Storage** | GCSバケットまたはローカルファイルシステムへの保存 |

---

## 6. JSONスキーマ仕様

### 6.1 出力ファイル命名規則

```
{article_id}_{YYYYMMDD}_{slug}.json
例: BttvaDsYEeet95PQUY-xEA_20260318_ai-robot-new-friend.json
```

### 6.2 JSONスキーマ

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "EngooArticle",
  "type": "object",
  "required": ["id", "meta", "exercises"],
  "properties": {
    "id": {
      "type": "string",
      "description": "Engoo記事の一意識別子"
    },
    "meta": {
      "type": "object",
      "required": ["title", "level", "url", "scraped_at", "published_date"],
      "properties": {
        "title":          { "type": "string" },
        "title_ja":       { "type": ["string", "null"], "description": "日本語タイトル（存在する場合）" },
        "level":          { "type": "string", "enum": ["Beginner", "Intermediate", "Advanced", "Unknown"] },
        "category":       { "type": ["string", "null"], "description": "記事カテゴリ（Science, Health等）" },
        "url":            { "type": "string", "format": "uri" },
        "thumbnail_url":  { "type": ["string", "null"] },
        "published_date": { "type": ["string", "null"], "description": "YYYY-MM-DD形式" },
        "scraped_at":     { "type": "string", "description": "ISO 8601形式の取得日時" }
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
                  "word":        { "type": "string" },
                  "phonetics":   { "type": ["string", "null"], "description": "発音記号" },
                  "part_of_speech": { "type": ["string", "null"], "description": "品詞 (noun, verb等)" },
                  "definition":  { "type": "string" },
                  "example":     { "type": ["string", "null"] }
                }
              }
            }
          }
        },
        "exercise_2_article": {
          "type": "object",
          "properties": {
            "label":    { "type": "string", "example": "Article" },
            "body":     { "type": "string", "description": "記事本文（段落を\\nで区切る）" },
            "paragraphs": {
              "type": "array",
              "items": { "type": "string" },
              "description": "段落ごとに分割した本文配列"
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

### 6.3 出力JSONサンプル

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

## 7. 機能要件

### 7.1 必須機能（Must Have）

| ID | 要件 |
|---|---|
| F-01 | 記事一覧ページから記事IDリストを取得できること |
| F-02 | Playwrightを使用して各記事ページのレンダリング済みHTMLを取得できること |
| F-03 | Exercise 1〜4を個別に抽出し、スキーマ準拠のJSONを生成できること |
| F-04 | 取得済み記事IDを管理し、重複取得をスキップできること（冪等性） |
| F-05 | JSONファイルを命名規則に従いローカルまたはGCSに保存できること |
| F-06 | 取得失敗時にエラーログを記録し、リトライ処理を行えること |

### 7.2 推奨機能（Should Have）

| ID | 要件 |
|---|---|
| F-07 | レベルフィルター指定（Beginnerのみ等）による選択的取得 |
| F-08 | カテゴリフィルター指定による選択的取得 |
| F-09 | 指定日付範囲の記事を一括取得するバルク取得モード |
| F-10 | JSONスキーマバリデーション（jsonschema等）による出力品質保証 |
| F-11 | 取得進捗のサマリーレポート出力（件数・成功/失敗・所要時間） |

### 7.3 将来検討（Nice to Have）

| ID | 要件 |
|---|---|
| F-12 | 内部API（XHR/Fetch）解析による高速取得モード |
| F-13 | 音声ファイルURL取得・保存 |
| F-14 | 取得したデータのLANGX評価スキーマへの自動変換 |
| F-15 | Cloud Run + Cloud Schedulerによるサーバーレス定期実行 |

---

## 8. 非機能要件

| 区分 | 要件 |
|---|---|
| **パフォーマンス** | 1記事あたりの取得・変換処理：30秒以内 |
| **スループット** | 並列ワーカー数：最大3（サーバー負荷配慮） |
| **リクエスト間隔** | 最低5秒（robots.txt準拠・スロットリング） |
| **可用性** | バッチ失敗時は自動リトライ（最大3回、指数バックオフ） |
| **データ整合性** | 取得済みIDのロック管理（並列実行での二重取得防止） |
| **ストレージ** | JSON 1件あたり約10〜50KB（年間見積もり：約18MB/年） |
| **ログ** | 取得日時・記事ID・ステータスを構造化ログ（JSON Lines）で保存 |

---

## 9. 実装スタック（推奨）

| レイヤー | 技術選定 | 理由 |
|---|---|---|
| スクレイピング | **Playwright (Python)** | SPA対応、ヘッドレス安定動作 |
| HTMLパース | **BeautifulSoup4 + lxml** | 高速・実績豊富 |
| スキーマバリデーション | **jsonschema** | Draft-07準拠 |
| ストレージ | **Google Cloud Storage** | 既存インフラ（GCP）との統合 |
| スケジューラ | **Cloud Scheduler + Cloud Run Jobs** | サーバーレス・低コスト |
| ログ管理 | **Google Cloud Logging** | 既存インフラとの統合 |
| 実行管理 | **Python 3.11+** | チーム標準 |

---

## 10. ディレクトリ構成

```
engoo-extractor/
├── README.md
├── pyproject.toml
├── .env.example
├── src/
│   ├── __init__.py
│   ├── config.py              # 環境変数・設定値
│   ├── scraper/
│   │   ├── index_scraper.py   # 記事一覧取得
│   │   └── content_fetcher.py # Playwright記事取得
│   ├── parser/
│   │   ├── html_parser.py     # HTML→構造データ変換
│   │   └── exercise_parser.py # Exercise別パーサー
│   ├── builder/
│   │   ├── json_builder.py    # JSONスキーマ変換
│   │   └── validator.py       # スキーマバリデーション
│   ├── storage/
│   │   ├── local_storage.py
│   │   └── gcs_storage.py
│   └── pipeline.py            # メインパイプライン
├── tests/
│   ├── fixtures/              # テスト用HTMLサンプル
│   ├── test_parser.py
│   └── test_builder.py
├── scripts/
│   ├── run_daily.sh           # 日次バッチ実行スクリプト
│   └── run_bulk.sh            # 一括取得スクリプト
└── output/                    # ローカル出力先（.gitignore対象）
    └── articles/
        └── {YYYY-MM}/
            └── {article_id}.json
```

---

## 11. エラーハンドリング仕様

| エラー種別 | 対応 |
|---|---|
| ページロードタイムアウト | 30秒タイムアウト設定、3回リトライ |
| HTMLパース失敗（要素未検出） | `null`値で保存 + 警告ログ出力 |
| JSONバリデーション失敗 | ファイル保存スキップ + エラーログ + Slackアラート |
| ネットワークエラー | 指数バックオフ（5s → 15s → 45s）でリトライ |
| レート制限（429） | 60秒待機後リトライ |
| ストレージ書き込み失敗 | ローカルフォールバック保存 |

---

## 12. 受け入れ基準（Acceptance Criteria）

| AC | 基準 |
|---|---|
| AC-01 | 指定した記事URLから、Exercise 1〜4の全フィールドを持つJSONが生成される |
| AC-02 | Vocabularyの各単語に `word` と `definition` が必ず含まれる |
| AC-03 | Article本文が段落単位で `paragraphs` 配列に分割されている |
| AC-04 | Discussion・Further Discussionの設問数が実際のページと一致する |
| AC-05 | 同一記事を2回実行しても重複JSONが生成されない（冪等性） |
| AC-06 | 100件の記事に対してバリデーション通過率95%以上 |

---

## 13. フェーズ計画

| フェーズ | 内容 | 期間目安 |
|---|---|---|
| **Phase 1** | Playwright環境構築 + 単一記事取得・パース PoC | 2日 |
| **Phase 2** | 記事一覧取得 + バッチ処理 + GCS保存 | 3日 |
| **Phase 3** | スキーマバリデーション + エラーハンドリング + ログ整備 | 2日 |
| **Phase 4** | Cloud Run定期実行 + Slackアラート統合 | 2日 |
| **Phase 5** | 過去記事一括取得（バルクモード） | 1日 |

---

## 14. 未解決事項・リスク

| 事項 | 内容 | 対応方針 |
|---|---|---|
| **利用規約確認** | スクレイピング可否の明示的確認が未完了 | Engoo社への問い合わせ、またはTOS精査 |
| **DOM構造変更リスク** | Engooがフロントエンドを更新した場合、パーサーが機能しなくなる可能性 | 定期的なパーサーテスト実行 + アラート設定 |
| **認証要件** | 一部コンテンツがログイン必須の場合、セッション管理が必要 | Cookieベースのセッション注入を実装 |
| **内部APIの特定** | XHR通信解析による直接API取得が可能か未確認 | Phase 1のPoC時に同時調査 |

---

*このPRDはEqumenopolis, Inc. 内部開発用ドキュメントです。外部共有不可。*
