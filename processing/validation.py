import config

VALID_SOURCES = {config.BOOKS_SOURCE, config.QUOTES_SOURCE}


def validate_record(record):
    problems = []
    source = record.get("source")

    if source not in VALID_SOURCES:
        problems.append("unknown_source")

    if not record.get("name_or_title"):
        problems.append("missing_name")

    url = str(record.get("source_url") or "")
    if not url.startswith(("http://", "https://")):
        problems.append("invalid_url")

    price = record.get("price")
    if price is not None and (not isinstance(price, (int, float)) or price < 0):
        problems.append("invalid_price")

    rating = record.get("rating")
    if rating is not None and rating not in (1, 2, 3, 4, 5):
        problems.append("invalid_rating")

    if source == config.BOOKS_SOURCE:
        if price is None:
            problems.append("missing_price")
        if rating is None:
            problems.append("missing_rating")

    if source == config.QUOTES_SOURCE and not record.get("author"):
        problems.append("missing_author")

    return problems
