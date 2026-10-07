import argparse
import csv
import json
import logging
import time
from collections import Counter
from datetime import datetime, timezone

import config
from processing.cleaning import clean_record
from processing.deduplication import find_duplicates
from processing.validation import validate_record
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper

logger = logging.getLogger("main")


def setup_logging():
    config.LOG_DIR.mkdir(exist_ok=True)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    file_handler = logging.FileHandler(config.LOG_DIR / "scraper.log", mode="w", encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(console_handler)


def parse_args():
    parser = argparse.ArgumentParser(description="Scrape, clean and consolidate books and quotes.")
    parser.add_argument("--details", action="store_true",
                        help="visit every book page to get category and description (slower)")
    parser.add_argument("--max-pages", type=int, default=None,
                        help="stop each source after this many listing pages")
    parser.add_argument("--delay", type=float, default=config.REQUEST_DELAY,
                        help="seconds to wait between requests")
    return parser.parse_args()


def run_source(scraper):
    stats = {
        "raw_collected": 0,
        "cleaned": 0,
        "rejected": 0,
        "rejected_by_reason": {},
        "duplicates_removed": 0,
        "final": 0,
        "error": None,
    }
    final_records = []

    try:
        raw_records = scraper.scrape()
    except Exception as error:
        logger.exception("%s: scraper crashed", scraper.source_name)
        stats["error"] = str(error)
        return final_records, stats

    stats["raw_collected"] = len(raw_records)
    reasons = Counter()

    valid_records = []
    for raw in raw_records:
        try:
            record = clean_record(raw)
        except Exception:
            logger.exception("Could not clean record: %s", raw)
            reasons["cleaning_error"] += 1
            stats["rejected"] += 1
            continue

        stats["cleaned"] += 1
        problems = validate_record(record)
        if problems:
            logger.warning("Rejected %s (%s): %s", record.get("name_or_title"), record.get("source_url"), problems)
            reasons.update(problems)
            stats["rejected"] += 1
        else:
            valid_records.append(record)

    final_records, duplicates = find_duplicates(valid_records)
    for record in duplicates:
        logger.warning("Duplicate removed: %s", record.get("name_or_title"))

    stats["rejected_by_reason"] = dict(reasons)
    stats["duplicates_removed"] = len(duplicates)
    stats["final"] = len(final_records)
    return final_records, stats


def write_csv(records, path):
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=config.COLUMNS)
        writer.writeheader()
        writer.writerows(records)


def write_summary(summary, path):
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4)


def main():
    args = parse_args()
    setup_logging()

    started = datetime.now(timezone.utc)
    timer = time.perf_counter()
    logger.info("Run started")

    scrapers = [
        BooksScraper(fetch_details=args.details, delay=args.delay, max_pages=args.max_pages),
        QuotesScraper(delay=args.delay, max_pages=args.max_pages),
    ]

    all_records = []
    source_stats = {}
    for scraper in scrapers:
        records, stats = run_source(scraper)
        all_records.extend(records)
        source_stats[scraper.source_name] = stats

    csv_path = config.OUTPUT_DIR / "final_dataset.csv"
    write_csv(all_records, csv_path)

    totals = {
        "raw_collected": sum(s["raw_collected"] for s in source_stats.values()),
        "cleaned": sum(s["cleaned"] for s in source_stats.values()),
        "rejected": sum(s["rejected"] for s in source_stats.values()),
        "duplicates_removed": sum(s["duplicates_removed"] for s in source_stats.values()),
        "final": len(all_records),
    }
    totals["reconciles"] = (
        totals["raw_collected"] - totals["rejected"] - totals["duplicates_removed"] == totals["final"]
    )

    summary = {
        "run": {
            "start_time": started.isoformat(timespec="seconds"),
            "end_time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "duration_seconds": round(time.perf_counter() - timer, 1),
            "book_details_fetched": args.details,
        },
        "sources": source_stats,
        "totals": totals,
    }
    write_summary(summary, config.OUTPUT_DIR / "summary_report.json")

    logger.info("Run finished: %d records written to %s", len(all_records), csv_path)
    if not totals["reconciles"]:
        logger.warning("Summary numbers do not add up, please check the log")


if __name__ == "__main__":
    main()
