from processing.deduplication import find_duplicates, make_fingerprint


def test_duplicates_ignore_case_and_spaces():
    base = {"source": "Books to Scrape", "author": None}
    records = [
        {**base, "name_or_title": "Example Book Title"},
        {**base, "name_or_title": "  Example Book Title "},
        {**base, "name_or_title": "EXAMPLE BOOK TITLE"},
    ]
    unique, duplicates = find_duplicates(records)
    assert len(unique) == 1
    assert len(duplicates) == 2


def test_duplicates_ignore_punctuation():
    base = {"source": "Books to Scrape", "author": None}
    records = [
        {**base, "name_or_title": "It's a Book!"},
        {**base, "name_or_title": "Its a Book"},
    ]
    unique, duplicates = find_duplicates(records)
    assert len(unique) == 1
    assert len(duplicates) == 1


def test_different_books_are_kept():
    base = {"source": "Books to Scrape", "author": None}
    records = [
        {**base, "name_or_title": "Book One"},
        {**base, "name_or_title": "Book Two"},
    ]
    unique, duplicates = find_duplicates(records)
    assert len(unique) == 2
    assert duplicates == []


def test_same_quote_text_with_different_author_is_kept():
    base = {"source": "Quotes to Scrape", "name_or_title": "Same words"}
    records = [{**base, "author": "Alice"}, {**base, "author": "Bob"}]
    unique, duplicates = find_duplicates(records)
    assert len(unique) == 2


def test_same_quote_same_author_is_duplicate():
    base = {"source": "Quotes to Scrape", "author": "Alice"}
    records = [
        {**base, "name_or_title": "Be kind to everyone you meet."},
        {**base, "name_or_title": "be  KIND to everyone you meet"},
    ]
    unique, duplicates = find_duplicates(records)
    assert len(duplicates) == 1


def test_same_title_in_two_sources_is_not_a_duplicate():
    a = {"source": "Books to Scrape", "name_or_title": "Shared", "author": None}
    b = {"source": "Quotes to Scrape", "name_or_title": "Shared", "author": None}
    assert make_fingerprint(a) != make_fingerprint(b)
