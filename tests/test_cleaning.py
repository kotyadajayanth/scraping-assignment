from processing.cleaning import (
    clean_price,
    clean_rating,
    clean_record,
    clean_tags,
    clean_text,
    normalize_url,
    strip_quotes,
)


def test_clean_text_collapses_whitespace():
    assert clean_text("  Hello \n World ") == "Hello World"


def test_clean_text_handles_non_breaking_space():
    assert clean_text("Hello\xa0\xa0World") == "Hello World"


def test_clean_text_empty_becomes_none():
    assert clean_text("   ") is None
    assert clean_text(None) is None


def test_strip_quotes_removes_curly_quotes():
    assert strip_quotes("\u201cThe world is round.\u201d") == "The world is round."


def test_clean_price():
    assert clean_price("\u00a351.77") == 51.77
    assert clean_price("\u00c2\u00a351.77") == 51.77
    assert clean_price("\u00a31,051.00") == 1051.0
    assert clean_price("free") is None
    assert clean_price(None) is None


def test_clean_rating():
    assert clean_rating("star-rating Three") == 3
    assert clean_rating("Five") == 5
    assert clean_rating("star-rating") is None
    assert clean_rating(None) is None


def test_clean_tags_sorted_lowercase_unique():
    assert clean_tags(["Love", " books ", "love"]) == "books;love"
    assert clean_tags([]) is None
    assert clean_tags(None) is None


def test_normalize_url_with_base():
    result = normalize_url("page-2.html", base="https://books.toscrape.com/catalogue/page-1.html")
    assert result == "https://books.toscrape.com/catalogue/page-2.html"


def test_clean_record_for_a_book():
    raw = {
        "source": "Books to Scrape",
        "source_url": "https://books.toscrape.com/catalogue/a_1/index.html",
        "name": "  A Light in the Attic ",
        "price": "\u00a351.77",
        "rating": "star-rating Three",
        "category": None,
        "description": None,
        "author": None,
        "tags": None,
    }
    record = clean_record(raw)
    assert record["name_or_title"] == "A Light in the Attic"
    assert record["price"] == 51.77
    assert record["rating"] == 3
    assert record["author"] is None


def test_clean_record_for_a_quote():
    raw = {
        "source": "Quotes to Scrape",
        "source_url": "https://quotes.toscrape.com/",
        "name": "\u201cSome quote.\u201d",
        "price": None,
        "rating": None,
        "category": None,
        "description": None,
        "author": " Albert Einstein ",
        "tags": ["Life", "change"],
    }
    record = clean_record(raw)
    assert record["name_or_title"] == "Some quote."
    assert record["author"] == "Albert Einstein"
    assert record["tags"] == "change;life"
    assert record["price"] is None
