# Multi-Source Web Scraping and Data Consolidation

A small ETL pipeline that scrapes two practice sites, cleans and validates the data, removes duplicates, and writes one CSV plus a JSON summary.

- Books to Scrape: https://books.toscrape.com/ (about 1,000 books, 50 pages)
- Quotes to Scrape: https://quotes.toscrape.com/ (100 quotes, 10 pages)

Pipeline: Scrape -> Clean -> Validate -> Deduplicate -> Consolidate -> Save

## Python version

Python 3.10, 3.11 or 3.12 (developed on 3.12).

## Setup

```
python -m venv venv
venv\Scripts\activate          (Windows)
source venv/bin/activate       (macOS / Linux)
pip install -r requirements.txt
```

## Dependencies

| Library | Why |
| --- | --- |
| requests | downloads pages, with retries |
| beautifulsoup4 + lxml | reads the HTML |
| pytest | unit tests |

Everything else (csv, json, logging, re, hashlib, argparse, pathlib) is in the standard library.

## How to run

```
python main.py
```

Optional arguments:

| Argument | Meaning |
| --- | --- |
| `--details` | open every book page to also collect category and description (about 1,000 extra requests, roughly 10 minutes) |
| `--max-pages N` | stop each source after N listing pages (useful for a quick test) |
| `--delay SECONDS` | pause between requests, default 0.5 |

Examples:

```
python main.py                       fast run, category and description stay empty for books
python main.py --details             full run, every field filled for books
python main.py --max-pages 2         quick test
```

Run the tests (no internet needed):

```
python -m pytest
```

## Output

| File | Content |
| --- | --- |
| `output/final_dataset.csv` | one row per valid, unique record from both sources |
| `output/summary_report.json` | counts per source and totals, rejection reasons, run time |
| `logs/scraper.log` | every page request, warning and error |

The summary numbers reconcile: `raw_collected - rejected - duplicates_removed = final`. The `reconciles` flag in the JSON shows this.

## Website observations

| Item | Books to Scrape | Quotes to Scrape |
| --- | --- | --- |
| One record | `article.product_pod` | `div.quote` |
| Main text | `h3 > a`, full title in the `title` attribute (visible text is cut with `...`) | `span.text`, wrapped in curly quotes |
| Price | `p.price_color` | none |
| Rating | class of `p.star-rating`, for example `Three` | none |
| Author | none | `small.author` |
| Tags | none | `a.tag`, zero or more |
| Next page | `li.next > a` | `li.next > a` |

Both sites are plain server-rendered HTML, so Requests + BeautifulSoup is enough. A browser tool such as Selenium would only add overhead.

## How pagination works

`BaseScraper.scrape()` starts at the home page, parses every record, then looks for `li.next > a`. If the link exists, it is turned into a full URL with `urljoin` and the loop continues. If it does not exist, the loop ends. Page numbers are never hard-coded, so the scraper still works if the site gets more or fewer pages.

## Data model

| Column | Books | Quotes |
| --- | --- | --- |
| source | Books to Scrape | Quotes to Scrape |
| source_url | book detail page URL | URL of the listing page where the quote appeared |
| name_or_title | book title | quote text (curly quotes removed) |
| category | from the detail page (needs `--details`), else empty | empty |
| price | number, for example 51.77 | empty |
| rating | integer 1 to 5 | empty |
| author | empty | author name |
| tags | empty | `tag1;tag2` (lowercase, sorted) |
| description | from the detail page (needs `--details`), else empty | empty |
| scraped_at | UTC timestamp | UTC timestamp |

Fields that do not apply are left empty. No values are invented. A quote has no page of its own, so the page it was found on is used as its URL.

## Cleaning approach

All cleaning lives in `processing/cleaning.py` as small functions that work on plain values, so they can be tested without internet:

- `clean_text`: collapses spaces, tabs, newlines and non-breaking spaces; empty text becomes `None`
- `strip_quotes`: removes the curly quotation marks around quote text
- `clean_price`: pulls the number out of text like `£51.77`
- `clean_rating`: turns the class text `star-rating Three` into `3`
- `clean_tags`: lowercase, remove repeats, sort, join with `;`
- `normalize_url`: trims and joins relative URLs
- `clean_record`: builds the final record in the common model

The page encoding is forced to UTF-8 so the `£` sign is read correctly.

## Validation approach

`validate_record` returns a list of problems. An empty list means the record is valid.

| Problem | Rule |
| --- | --- |
| unknown_source | source must be one of the two known names |
| missing_name | name_or_title must not be empty |
| invalid_url | source_url must start with http:// or https:// |
| invalid_price | price, if present, must be a number >= 0 |
| invalid_rating | rating, if present, must be 1 to 5 |
| missing_price / missing_rating | required for books |
| missing_author | required for quotes |

Rejected records are logged as warnings and counted by reason in the summary. The program keeps running.

## Deduplication approach

Each record gets a fingerprint: the identifying fields are joined, lowercased, stripped of punctuation, spaces collapsed, then hashed with SHA-256.

- Books: source + title
- Quotes: source + author + first 50 characters of the quote

So `"Example Book Title"`, `" Example Book Title "` and `"EXAMPLE BOOK TITLE"` all give the same fingerprint. Duplicates are removed rather than flagged, because the final file should have one row per real item, and every removed duplicate is logged and counted in the summary. The two real sites contain no duplicates, so the logic is proved by the unit tests in `tests/test_deduplication.py`.

## Error-handling approach

- `requests.Session` retries HTTP 429, 500, 502, 503 and 504 up to 3 times with growing delays (backoff).
- Every request has a 10 second timeout.
- If a page cannot be loaded after retries, the error is logged and that source stops, keeping the records collected so far.
- Each source runs inside its own `try/except`, so one source failing does not stop the other.
- Each record is parsed inside `try/except`; missing HTML elements give `None` instead of crashing.
- A failed book detail page only leaves category and description empty for that book.

## Assumptions

- The sites keep their current HTML structure.
- Quote identity is author plus the first 50 characters of the text.
- Prices are in GBP and stored as plain numbers.

## Known limitations

- Without `--details`, category and description are empty for books, because the listing page does not show them.
- The scraper is sequential, so a full `--details` run takes around 10 minutes because of the polite 0.5 second pause.
- If a listing page fails after all retries, later pages of that source are skipped, because the next link is only found on the page that failed.
- No resume or checkpoint feature.

## AI usage summary

See `AI_USAGE.md`.

## Project structure

```
scraping_assignment/
├── scrapers/        base_scraper.py, books_scraper.py, quotes_scraper.py
├── processing/      cleaning.py, validation.py, deduplication.py
├── tests/           unit tests, no internet needed
├── output/          final_dataset.csv, summary_report.json
├── logs/            scraper.log
├── config.py        URLs, delay, timeout, column order
├── main.py          runs the whole pipeline
├── requirements.txt
├── README.md
└── AI_USAGE.md
```
