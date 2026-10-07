from processing.validation import validate_record


def good_book():
    return {
        "source": "Books to Scrape",
        "source_url": "https://books.toscrape.com/catalogue/a_1/index.html",
        "name_or_title": "A Book",
        "price": 10.5,
        "rating": 4,
        "author": None,
    }


def good_quote():
    return {
        "source": "Quotes to Scrape",
        "source_url": "https://quotes.toscrape.com/",
        "name_or_title": "A quote",
        "price": None,
        "rating": None,
        "author": "Someone",
    }


def test_valid_records_have_no_problems():
    assert validate_record(good_book()) == []
    assert validate_record(good_quote()) == []


def test_unknown_source():
    record = good_book()
    record["source"] = "Other Site"
    assert "unknown_source" in validate_record(record)


def test_missing_name_and_bad_url():
    record = good_book()
    record["name_or_title"] = None
    record["source_url"] = "not-a-url"
    problems = validate_record(record)
    assert "missing_name" in problems
    assert "invalid_url" in problems


def test_negative_price():
    record = good_book()
    record["price"] = -1
    assert "invalid_price" in validate_record(record)


def test_zero_price_is_allowed():
    record = good_book()
    record["price"] = 0
    assert validate_record(record) == []


def test_rating_out_of_range():
    record = good_book()
    record["rating"] = 7
    assert "invalid_rating" in validate_record(record)


def test_book_needs_price_and_rating():
    record = good_book()
    record["price"] = None
    record["rating"] = None
    problems = validate_record(record)
    assert "missing_price" in problems
    assert "missing_rating" in problems


def test_quote_needs_author():
    record = good_quote()
    record["author"] = None
    assert "missing_author" in validate_record(record)
