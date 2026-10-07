import hashlib
import re

import config


def make_fingerprint(record):
    source = record.get("source") or ""
    name = record.get("name_or_title") or ""

    if source == config.QUOTES_SOURCE:
        author = record.get("author") or ""
        key = f"{source} {author} {name[:50]}"
    else:
        key = f"{source} {name}"

    key = re.sub(r"[^\w\s]", "", key.lower())
    key = " ".join(key.split())
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def find_duplicates(records):
    seen = set()
    unique = []
    duplicates = []

    for record in records:
        fingerprint = make_fingerprint(record)
        if fingerprint in seen:
            duplicates.append(record)
        else:
            seen.add(fingerprint)
            unique.append(record)

    return unique, duplicates
