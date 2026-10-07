import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import config

RATING_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}


def clean_text(value):
    if value is None:
        return None
    text = " ".join(str(value).replace("\xa0", " ").split())
    return text or None


def strip_quotes(value):
    text = clean_text(value)
    if text is None:
        return None
    text = text.strip("\u201c\u201d\"").strip()
    return text or None


def clean_price(raw):
    if raw is None:
        return None
    match = re.search(r"\d+(?:\.\d+)?", str(raw).replace(",", ""))
    if match is None:
        return None
    return float(match.group())


def clean_rating(raw):
    if raw is None:
        return None
    for word in str(raw).lower().split():
        if word in RATING_WORDS:
            return RATING_WORDS[word]
    return None


def clean_tags(tags):
    if not tags:
        return None
    cleaned = {clean_text(tag).lower() for tag in tags if clean_text(tag)}
    if not cleaned:
        return None
    return ";".join(sorted(cleaned))


def normalize_url(url, base=None):
    url = clean_text(url)
    if url is None:
        return None
    if base:
        url = urljoin(base, url)
    return url


def clean_record(raw):
    source = clean_text(raw.get("source"))
    name = clean_text(raw.get("name"))
    if source == config.QUOTES_SOURCE:
        name = strip_quotes(name)

    return {
        "source": source,
        "source_url": normalize_url(raw.get("source_url")),
        "name_or_title": name,
        "category": clean_text(raw.get("category")),
        "price": clean_price(raw.get("price")),
        "rating": clean_rating(raw.get("rating")),
        "author": clean_text(raw.get("author")),
        "tags": clean_tags(raw.get("tags")),
        "description": clean_text(raw.get("description")),
        "scraped_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
